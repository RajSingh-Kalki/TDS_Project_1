Here is the Python code that will connect to the SQLite database `ticket-sales.db`, compute the total sales for the "Gold" ticket type, and write the result to the file `/data/ticket-sales-gold.txt`.

```python
import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('/data/ticket-sales.db')
cursor = conn.cursor()

# Query to calculate the total sales for "Gold" ticket type
query = """
SELECT SUM(units * price) AS total_sales
FROM tickets
WHERE type = 'Gold';
"""

# Execute the query
cursor.execute(query)

# Fetch the result
result = cursor.fetchone()
total_sales = result[0] if result[0] is not None else 0

# Write the total sales to the output file
with open('/data/ticket-sales-gold.txt', 'w') as f:
    f.write(str(total_sales))

# Clean up
cursor.close()
conn.close()
```

### Instructions:
1. Make sure that the `sqlite3` library is installed in your Python environment. This is usually included with Python's standard library, so it should be available by default.
2. Ensure the paths to the database and output file are correct according to your file system.
3. Run the script, and it will create the output file `ticket-sales-gold.txt` containing the total sales for "Gold" tickets.