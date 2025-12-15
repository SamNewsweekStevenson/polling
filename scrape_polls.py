"""
Script to scrape polling data table from test.html using BeautifulSoup.
Extracts the table with 'pollster' as the first header column.
"""

from bs4 import BeautifulSoup
import json
import re
import csv


def extract_poll_table(html_file):
    """
    Extract polling data from the HTML file.
    The data is stored in JSON format within script tags (React/Next.js).
    """
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Primary method: Extract from embedded JSON data (React/Next.js pages)
    # The table content is rendered via JavaScript, so we need the JSON source
    polls_data = extract_all_polls(html_content)
    if polls_data:
        return format_polls_data(polls_data)
    
    # Fallback: Try to find table directly (if server-rendered)
    tables = soup.find_all('table')
    
    for table in tables:
        # Find the table with 'pollster' header
        headers = table.find_all('th')
        header_texts = [h.get_text(strip=True).lower() for h in headers]
        
        if header_texts and header_texts[0] == 'pollster':
            print(f"Found table with headers: {header_texts}")
            
            # Extract rows from tbody
            rows = []
            tbody = table.find('tbody')
            if tbody:
                for tr in tbody.find_all('tr'):
                    cells = tr.find_all(['td', 'th'])
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data and len(row_data) > 1:  # Skip single-cell rows
                        rows.append(row_data)
            
            if rows:
                return header_texts, rows
    
    return None, None


def extract_json_polls(html_content, start_pos=0):
    """
    Extract poll data from embedded JSON in the HTML starting from a given position.
    RealClearPolitics stores data in escaped JSON format within script tags.
    The JSON uses escaped quotes like: \"pollster\":\"Rasmussen Reports\"
    
    Args:
        html_content: The HTML content to parse
        start_pos: Position to start searching from (default 0)
    
    Returns:
        tuple: (polls_list, end_position) or (None, -1) if not found
    """
    # Find the start of the polls array (escaped format)
    polls_start = html_content.find('\\"polls\\":[', start_pos)
    
    if polls_start == -1:
        # Try unescaped format
        polls_start = html_content.find('"polls":[', start_pos)
        if polls_start == -1:
            return None, -1
        array_start = polls_start + len('"polls":')
        escaped = False
    else:
        array_start = polls_start + len('\\"polls\\":')
        escaped = True
    
    # Find the matching closing bracket for the array
    bracket_count = 0
    in_string = False
    i = array_start
    
    while i < len(html_content):
        char = html_content[i]
        
        # Handle escaped quotes in escaped JSON
        if escaped and i + 1 < len(html_content) and html_content[i:i+2] == '\\"':
            if not in_string:
                in_string = True
            else:
                in_string = False
            i += 2
            continue
        
        # Handle regular quotes
        if not escaped and char == '"':
            # Check for escape
            if i > 0 and html_content[i-1] == '\\':
                pass  # escaped quote, ignore
            else:
                in_string = not in_string
        
        if not in_string:
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    json_str = html_content[array_start:i + 1]
                    
                    # Unescape if needed
                    if escaped:
                        json_str = json_str.replace('\\"', '"')
                        json_str = json_str.replace('\\\\', '\\')
                    
                    try:
                        polls = json.loads(json_str)
                        # Filter out non-dict items (references like "$1f:2:props...")
                        polls = [p for p in polls if isinstance(p, dict)]
                        return polls, i + 1
                    except json.JSONDecodeError as e:
                        print(f"JSON parse error: {e}")
                        return None, -1
        
        i += 1
    
    return None, -1


def extract_all_polls(html_content):
    """
    Extract all polls arrays from the HTML content.
    Returns a combined list of all poll data.
    """
    all_polls = []
    start_pos = 0
    table_num = 1
    
    while True:
        polls, end_pos = extract_json_polls(html_content, start_pos)
        if polls is None:
            break
        
        print(f"Table {table_num}: Found {len(polls)} polls")
        all_polls.extend(polls)
        table_num += 1
        start_pos = end_pos
    
    return all_polls if all_polls else None


def format_polls_data(polls):
    """
    Format the polls data into a table structure.
    """
    headers = ['pollster', 'date', 'sample', 'approve', 'disapprove', 'spread']
    rows = []
    
    for poll in polls:
        pollster = poll.get('pollster', poll.get('pollster_group_name', ''))
        date = poll.get('date', '')
        sample = poll.get('sampleSize', '')
        
        # Extract candidate values (Approve/Disapprove)
        candidates = poll.get('candidate', [])
        approve = ''
        disapprove = ''
        
        for candidate in candidates:
            name = candidate.get('name', '').lower()
            value = candidate.get('value', '')
            if 'approve' in name and 'disapprove' not in name:
                approve = value
            elif 'disapprove' in name:
                disapprove = value
        
        # Extract spread
        spread_data = poll.get('spread', {})
        spread = spread_data.get('value', '') if isinstance(spread_data, dict) else ''
        
        rows.append([pollster, date, sample, approve, disapprove, spread])
    
    return headers, rows


def save_to_csv(headers, rows, output_file='poll_data.csv'):
    """
    Save extracted data to CSV file.
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Data saved to {output_file}")


def main():
    html_file = 'test.html'
    
    print(f"Extracting poll data from {html_file}...")
    headers, rows = extract_poll_table(html_file)
    
    if headers and rows:
        print(f"\nHeaders: {headers}")
        print(f"Found {len(rows)} rows of data\n")
        
        # Print first few rows
        print("First 5 rows:")
        print("-" * 80)
        for row in rows[:5]:
            print(row)
        print("-" * 80)
        
        # Save to CSV
        save_to_csv(headers, rows)
    else:
        print("No poll data found in the HTML file.")


if __name__ == '__main__':
    main()
