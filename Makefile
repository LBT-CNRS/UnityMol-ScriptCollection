# Makefile for status

.PHONY: info

info:
	clear
	@printf "\ninfo:: UnityMol Scripts Collection\n\n"
	@printf "info:: common targets: info, doc\n"
	@ls -GF
	@git status .

doc:
	@cat README.org
