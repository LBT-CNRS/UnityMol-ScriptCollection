from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion, abstractmethod
from prompt_toolkit.document import Document
import os
import re
import zmq
import json
import inspect
import math

class UnityMolAutoSuggest(AutoSuggest):
    """
    Custom auto-suggester inspired by Unity's autocompletion logic.
    Provides suggestions for:
    1. API functions
    2. Loaded molecules and selections
    3. File paths when appropriate
    """
    def __init__(self, socket=None):
        self.api_functions = []
        self.loaded_structures = []
        self.current_choices = []
        self.current_input = ""
        self.choice_index = 0
        self.tab_pressed = False
        self.socket = socket
        
        # Load API functions
        self._load_api_functions()
    
    def _load_api_functions(self):
        """Load available API functions from ZMQ server or local imports"""
        try:
            # Try to query server for available functions
            if self.socket:
                self.socket.send_string("get_api_functions()")
                reply = self.socket.recv().decode()
                data = json.loads(reply)
                if data.get("success", False):
                    self.api_functions = data.get("result", [])
            
            # Fallback to common UnityMol Python functions
            if not self.api_functions:
                common_functions = [
                    "load", "load_pdb", "load_mol2", "load_sdf", "load_mol", "save",
                    "delete", "select", "show", "hide", "color", "representation",
                    "center_on_selection", "measure_distance", "measure_angle",
                    "measure_dihedral", "list_selections", "list_representations",
                    "list_molecules", "help"
                ]
                self.api_functions = common_functions
        except Exception as e:
            print(f"Error loading API functions: {e}")
            self.api_functions = []

    def _get_loaded_structures(self):
        """Query ZMQ server for loaded molecules and selections"""
        try:
            if self.socket:
                self.socket.send_string("list_selections(); list_molecules()")
                reply = self.socket.recv().decode()
                data = json.loads(reply)
                if data.get("success", False):
                    result = data.get("result", "")
                    # Parse result to extract molecule and selection names
                    # This is a simplified approach - adjust based on actual output format
                    names = re.findall(r'[\'"]([^\'"]+)[\'"]', result)
                    return names
        except Exception as e:
            print(f"Error getting structures: {e}")
        return []

    def _get_possible_paths(self, starting_path, limit=500):
        """Get possible file/directory completions for path"""
        results = []
        
        if not starting_path or "~" in starting_path:  # Skip if empty or contains ~ (for now)
            return results
            
        try:
            # Get absolute path and directory
            abs_path = os.path.abspath(os.path.expanduser(starting_path))
            dir_name = os.path.dirname(abs_path)
            
            # Get directories
            if os.path.isdir(dir_name):
                # Add directories
                dirs = [os.path.join(dir_name, d).replace("\\", "/") 
                        for d in os.listdir(dir_name) 
                        if os.path.isdir(os.path.join(dir_name, d))]
                results.extend(dirs[:limit])
                
                if len(results) >= limit:
                    return results
                    
                # Add files
                files = [os.path.join(dir_name, f).replace("\\", "/") 
                         for f in os.listdir(dir_name) 
                         if os.path.isfile(os.path.join(dir_name, f))]
                results.extend(files[:limit - len(results)])
        except Exception as e:
            pass  # Silently fail as in the original code
            
        return results

    def _extract_quote_content(self, text):
        """Extract content inside quotes for path/molecule completion"""
        # Find the last quote (single or double)
        double_quote_idx = text.rfind('"')
        single_quote_idx = text.rfind("'")
        
        # Get the position after the last quote
        quote_pos = max(double_quote_idx, single_quote_idx)
        
        if quote_pos < 0:
            return None, -1
            
        # Return substring after quote
        return text[quote_pos + 1:], quote_pos + 1

    def _fuzzy_match(self, string_to_search, pattern):
        """Implementation of the FuzzyMatch algorithm from the Unity code"""
        # Score constants
        adjacency_bonus = 5
        separator_bonus = 10
        camel_bonus = 10
        leading_letter_penalty = -3
        max_leading_letter_penalty = -9
        unmatched_letter_penalty = -1
        
        # Loop variables
        score = 0
        pattern_idx = 0
        pattern_length = len(pattern)
        str_idx = 0
        str_length = len(string_to_search)
        prev_matched = False
        prev_lower = False
        prev_separator = True  # True if first letter match gets separator bonus
        
        # Best match tracking
        best_letter = None
        best_lower = None
        best_letter_idx = None
        best_letter_score = 0
        matched_indices = []
        
        # Loop over strings
        while str_idx < str_length:
            pattern_char = pattern[pattern_idx] if pattern_idx < pattern_length else None
            str_char = string_to_search[str_idx]
            
            pattern_lower = pattern_char.lower() if pattern_char else None
            str_lower = str_char.lower()
            str_upper = str_char.upper()
            
            next_match = pattern_char is not None and pattern_lower == str_lower
            rematch = best_letter is not None and best_lower == str_lower
            
            advanced = next_match and best_letter is not None
            pattern_repeat = (best_letter is not None and pattern_char is not None 
                             and best_lower == pattern_lower)
                             
            if advanced or pattern_repeat:
                score += best_letter_score
                matched_indices.append(best_letter_idx)
                best_letter = None
                best_lower = None
                best_letter_idx = None
                best_letter_score = 0
            
            if next_match or rematch:
                new_score = 0
                
                # Apply penalty for leading letters
                if pattern_idx == 0:
                    penalty = max(str_idx * leading_letter_penalty, max_leading_letter_penalty)
                    score += penalty
                
                # Apply bonuses
                if prev_matched:
                    new_score += adjacency_bonus
                    
                if prev_separator:
                    new_score += separator_bonus
                    
                if prev_lower and str_char == str_upper and str_lower != str_upper:
                    new_score += camel_bonus
                    
                # Update pattern index for next match
                if next_match:
                    pattern_idx += 1
                    
                # Update best letter
                if new_score >= best_letter_score:
                    # Apply penalty for skipped letter
                    if best_letter is not None:
                        score += unmatched_letter_penalty
                        
                    best_letter = str_char
                    best_lower = str_char.lower()
                    best_letter_idx = str_idx
                    best_letter_score = new_score
                    
                prev_matched = True
            else:
                score += unmatched_letter_penalty
                prev_matched = False
                
            # Update state for next iteration
            prev_lower = str_char == str_lower and str_lower != str_upper
            prev_separator = str_char in ('_', ' ')
            
            str_idx += 1
            
        # Apply score for last match
        if best_letter is not None:
            score += best_letter_score
            matched_indices.append(best_letter_idx)
            
        return score

    def _auto_complete_text(self, input_text, source_list, max_shown=8, levenshtein_distance=0.5):
        """Python implementation of AutoCompleteText from Unity code"""
        result = []
        sorted_results = []
        
        if not input_text or len(input_text) < 2 or len(input_text) >= 200:
            return result
            
        keywords = input_text
        unique_src = list(set(source_list))  # Using a list instead of HashSet
        
        # First pass: exact prefix matches (starts with)
        for i, item in enumerate(source_list):
            if len(result) == max_shown:
                return result
                
            if item.startswith(keywords):
                result.append(i)
                if item in unique_src:
                    unique_src.remove(item)
                    
        if len(result) == max_shown:
            return result
            
        # Second pass: contains matches
        to_remove = []
        for s in unique_src:
            if len(result) == max_shown:
                return result
                
            if keywords in s:
                idx = source_list.index(s)
                result.append(idx)
                to_remove.append(s)
                
        if len(result) == max_shown:
            return result
            
        for s in to_remove:
            if s in unique_src:
                unique_src.remove(s)
                
        # Third pass: fuzzy matches
        fuzzy_results = []
        for i, s in enumerate(unique_src):
            score = self._fuzzy_match(s, keywords)
            if score > 1.5 * len(input_text):
                fuzzy_results.append((source_list.index(s), score))
                
        # Sort by score (descending)
        fuzzy_results.sort(key=lambda x: x[1], reverse=True)
        
        # Add top fuzzy matches
        for idx, _ in fuzzy_results:
            if len(result) == max_shown:
                break
            result.append(idx)
            
        return result

    @abstractmethod
    def get_suggestion(self, buffer, document):
        """Main method to get suggestions for prompt_toolkit"""
        text = document.text
        cursor_position = document.cursor_position
        
        # Don't provide suggestions when the buffer is empty
        if not text:
            self.current_choices = []
            return None
            
        # Check if Tab was just pressed (document ends with Tab character)
        tab_pressed = False
        if text.endswith("\t"):
            tab_pressed = True
            text = text[:-1]  # Remove tab character for processing
            
        # If the input changed, reset the choices
        if text != self.current_input and not tab_pressed:
            self.current_input = text
            self.choice_index = 0
            self.tab_pressed = False
            
            # Determine what to autocomplete
            if "(" in text and not text.endswith(")"):
                # Complete molecule names, selections, or paths
                content, pos = self._extract_quote_content(text)
                
                if pos != -1:
                    sources = self._get_loaded_structures()
                    
                    # Check if we're in a load/export command to offer path completions
                    if any(text.startswith(cmd) for cmd in ["load", "export", "read"]):
                        paths = self._get_possible_paths(content)
                        if paths:
                            sources.extend(paths)
                    
                    if content and sources:
                        matches = self._auto_complete_text(content, sources)
                        self.current_choices = [(idx, sources[idx]) for idx in matches]
            else:
                # Complete API function names
                matches = self._auto_complete_text(text, self.api_functions)
                self.current_choices = [(idx, self.api_functions[idx]) for idx in matches]
        
        # If Tab was pressed and we have choices, cycle through them
        if tab_pressed and self.current_choices:
            if self.tab_pressed:
                # Move to next choice
                self.choice_index = (self.choice_index + 1) % len(self.current_choices)
            
            # Get the current choice
            _, suggestion_text = self.current_choices[self.choice_index]
            
            # For function names, replace the entire text
            if "(" not in text or text.endswith(")"):
                self.tab_pressed = True
                return Suggestion(suggestion_text[len(text):])
            
            # For quotes content, replace only what's after the quote
            else:
                content, pos = self._extract_quote_content(text)
                if pos != -1:
                    self.tab_pressed = True
                    # Only replace what's after the quote position
                    prefix = text[:pos]
                    return Suggestion(suggestion_text[len(content):])
        
        # If we have choices but Tab wasn't pressed, suggest the first choice
        elif self.current_choices and not self.tab_pressed:
            _, suggestion_text = self.current_choices[0]
            
            # For function names
            if "(" not in text or text.endswith(")"):
                # Only suggest if it's a prefix match
                if suggestion_text.startswith(text):
                    return Suggestion(suggestion_text[len(text):])
            
            # For quotes content
            else:
                content, pos = self._extract_quote_content(text)
                if pos != -1 and content and suggestion_text.startswith(content):
                    return Suggestion(suggestion_text[len(content):])
        
        return None


# You can use it like this:
# socket = zmq.Context.instance().socket(zmq.REQ)
# socket.connect("tcp://localhost:5555")
# session = PromptSession(
#     "> ",
#     multiline=True,
#     key_bindings=kb,
#     history=history,
#     auto_suggest=UnityMolAutoSuggest(socket),
# )
