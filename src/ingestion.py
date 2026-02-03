

file_path = 'data/sample.txt' 
try:
    with open(file_path, 'r') as file:
        content = file.read()
    print(content)
except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found.")
