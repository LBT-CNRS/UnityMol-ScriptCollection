# unitymol_zmq.py
# UnityMol Development Script
# (c) 2025 by Marc BAADEN
# MIT license

"""
UnityMol ZMQ Communication Module

This module handles communication with UnityMol through its ZMQ server.
It provides functions to send commands and receive responses.
"""

__version__ = "0.1.0"

import zmq
import json
import logging

unitymol = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UnityMolZMQ")

class UnityMolZMQ:
    """
    Class to handle ZMQ communication with UnityMol.
    """
    
    # Default connection settings
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 5555
    
    def __init__(self, host=None, port=None):
        """
        Initialize the ZMQ connection to UnityMol.
        
        Args:
            host (str): The host where UnityMol is running
            port (int): The port on which UnityMol's ZMQ server is listening
        """
        self.host = host or self.DEFAULT_HOST
        self.port = port or self.DEFAULT_PORT
        self.context = zmq.Context.instance()
        self.socket = None
        self.connected = False
        
    def connect(self, timeout=10):
        """
        Establish connection to UnityMol's ZMQ server.

        Args:
            timeout (int): Timeout value in seconds

        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            self.socket = self.context.socket(zmq.REQ)
            self.socket.setsockopt(zmq.LINGER, 0)  # Don't block at the end
            self.socket.connect(f"tcp://{self.host}:{self.port}")

            # Send a test message
            self.socket.send_string("import sys")

           # Poll the socket with timeout
            poller = zmq.Poller()
            poller.register(self.socket, zmq.POLLIN)
            socks = dict(poller.poll(timeout * 1000))  # Timeout in milliseconds

            if socks.get(self.socket) == zmq.POLLIN:
                reply = json.loads(self.socket.recv().decode())

                if reply['success']:
                    self.connected = True
                    logger.info(f"server connected OK to tcp://{self.host}:{self.port}.\n")
                    return True
                else:
                    logger.error(f"server bad response from tcp://{self.host}:{self.port}.\n")
            else:
                logger.error(f"server at tcp://{self.host}:{self.port} did not respond.\n")
                
        except zmq.error.ZMQError as e:
            logger.error(f"Failed to connect to UnityMol ZMQ server: {e}\n")

        self.connected = False
        return False
    
    def disconnect(self):
        """
        Close the connection to UnityMol's ZMQ server.
        """
        if self.socket:
            self.socket.close()
            self.connected = False
            logger.info("Disconnected from UnityMol ZMQ server")
    
    def send_command(self, command):
        """
        Send a command to UnityMol and receive the response.
        
        Args:
            command (str): The UnityMol API command to execute
            
        Returns:
            dict: A dictionary containing the response with keys:
                - success (bool): Whether the command was successful
                - result (str): The result of the command
                - stdout (str): Additional output from the command
                
        Raises:
            ConnectionError: If not connected to UnityMol
            TimeoutError: If the command times out
            ValueError: If the response is not valid JSON
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError("Not connected to UnityMol ZMQ server")
        
        try:
            logger.debug(f"Sending command: {command}")
            self.socket.send_string(command)
            response = self.socket.recv().decode()
            
            try:
                # Try to parse as JSON
                result = json.loads(response)
                logger.debug(f"Received response: {result}")
                return result
            except json.JSONDecodeError:
                # If not valid JSON, create a simple result structure
                logger.warning(f"Received non-JSON response: {response}")
                # Handle the case where response is just "True" or "False"
                if response.strip().lower() == "true":
                    return {"success": True, "result": "Command succeeded", "stdout": ""}
                elif response.strip().lower() == "false":
                    return {"success": False, "result": "", "stdout": "Command failed"}
                else:
                    return {"success": True, "result": response, "stdout": ""}
                
        except zmq.error.Again:
            logger.error("Command timed out")
            raise TimeoutError("Command to UnityMol timed out")
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            raise
    
    def test_connection(self):
        """
        Test the connection to UnityMol by sending a simple command.
        
        Returns:
            bool: True if the connection is working, False otherwise
        """
        try:
            # Use a simple command that should always work if UnityMol is running
            
            # Envoyer un message de test
            reply = self.send_command("import System")
            if reply['success']:
                # If we got any response, consider the connection successful
                return True

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
