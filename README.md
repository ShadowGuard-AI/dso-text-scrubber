![Banner](banner.png)

# dso-text-scrubber
A command-line tool that removes or replaces sensitive information (e.g., email addresses, phone numbers, dates, common PII patterns) from text files. Utilizes regular expressions for pattern matching, allowing customizable patterns. Operates on standard input/output or file-based input/output. - Focused on Tools for sanitizing and obfuscating sensitive data within text files and structured data formats, preparing datasets for testing or secure sharing.

## Install
`git clone https://github.com/ShadowStrikeHQ/dso-text-scrubber`

## Usage
`python3 main.py -i input.txt -o output.txt [-r remove|fake|custom] [-c replacement] [-p pattern ...]`

Notes on behaviour:
- If the resolved output path is the input file (same path, a ./ alias, or a symlink to it), the run refuses at exit 1 before anything is written and the input is unchanged.
- Every pattern is compiled at startup. A pattern that does not compile fails the run at exit 1 before any output is opened.
- Custom mode (`-r custom`) requires `-c`; without it the run exits 1.
- The run counts matches. If nothing is scrubbed, it prints a plain no values scrubbed line and exits 1, and no output file is written.
- Fake mode generates a value of the matched pattern type (email, phone, date, or name) instead of a plain word for every match.
- Default name pattern limits: it matches two capitalised words in a row, with a guard so a pair starting with a common article or determiner such as The, A, An, This, or That is left alone, so an ordinary pair such as The Report survives. It will still match other capitalised pairs that are not personal names, and it misses names that are not two capitalised words in a row. Treat it as a simple pattern, not name recognition.

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
