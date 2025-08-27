import os

print(os.path.exists("data"))            # Should print True
print(os.path.exists("data/items.csv"))  # Should print True if file is correct
print(os.listdir("data"))                # Lists all files inside data
