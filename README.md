# dso-text-scrubber
A command-line tool that removes or replaces sensitive information (e.g., email addresses, phone numbers, dates, common PII patterns) from text files. Utilizes regular expressions for pattern matching, allowing customizable patterns. Operates on standard input/output or file-based input/output. - Focused on Tools for sanitizing and obfuscating sensitive data within text files and structured data formats, preparing datasets for testing or secure sharing.

## Install
`git clone https://github.com/ShadowStrikeHQ/dso-text-scrubber`

## Usage
`./dso-text-scrubber [params]`

## Parameters
- `-h`: Show help message and exit
- `-i`: Input file path, use - for stdin
- `-o`: Output file path, use - for stdout
- `-p`: Regex patterns for sensitive data.
- `-r`: No description provided
- `-c`: Custom replacement string if replacement type is 
- `--version`: No description provided

## License
Copyright (c) ShadowStrikeHQ
