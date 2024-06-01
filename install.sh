#!/bin/bash

# Path to the activation script
FILE="django-vue/bin/activate"

# New virtual environment path
NEW_VIRTUAL_ENV_PATH="$(pwd)/django-vue"

# Backup the original file
cp "$FILE" "${FILE}.bak"

# Update VIRTUAL_ENV variable
sed -i "s|^VIRTUAL_ENV=.*|VIRTUAL_ENV=\"$NEW_VIRTUAL_ENV_PATH\"|" "$FILE"

echo "VIRTUAL_ENV updated in $FILE"

# Directory containing the files
DIRECTORY="django-vue/bin"

# New shebang line with the current directory's Python path
NEW_SHEBANG="#!$(pwd)/django-vue/bin/python3"

# Loop through each file in the directory
for FILE in "$DIRECTORY"/*
do
    filename=$(basename "$FILE")
    
    # Check if the file is a regular file (not a directory or other type of file)
    if [ -f "$FILE" ] && ([[ "$filename" == "pip" ]] || [[ "$filename" == "pip3" ]] || [[ "$filename" == "pip3.8" ]] || [[ "$filename" == "django-admin" ]] ); then
        # Backup the original file
        cp "$FILE" "${FILE}.bak"
        # Use sed to replace the first line
	sed -i "1s|.*|$NEW_SHEBANG|" "$FILE"
	echo "Updated in $FILE"
    fi
done

