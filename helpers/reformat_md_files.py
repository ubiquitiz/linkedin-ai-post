import markdown
import re
from bs4 import BeautifulSoup

def convert_md_to_linkedin_format(md_content):
    """
    Convert Markdown to a LinkedIn-compatible text format.
    LinkedIn doesn't support Markdown directly, so we need to
    convert to a format that looks good on LinkedIn.
    """
    # Convert Markdown to HTML
    html_content = markdown.markdown(md_content)

    # Use BeautifulSoup to help with text extraction and special handling
    soup = BeautifulSoup(html_content, 'html.parser')

    # Handle headings (LinkedIn uses no special formatting, just make them bold)
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        # Create bold text with newlines around it
        bold = soup.new_tag('strong')
        bold.string = heading.text
        # Replace heading with bold text and add newlines
        heading.replace_with(bold)

    # Handle lists
    for ul in soup.find_all('ul'):
        # Replace each list item with a • character
        for li in ul.find_all('li'):
            li.replace_with(f"• {li.text}\n")
        # Add newline after list
        ul.replace_with('\n' + ul.text + '\n')

    # Handle numbered lists
    for ol in soup.find_all('ol'):
        for i, li in enumerate(ol.find_all('li')):
            li.replace_with(f"{i + 1}. {li.text}\n")
        # Add newline after list
        ol.replace_with('\n' + ol.text + '\n')

    # Convert back to text
    linkedin_text = soup.get_text()

    # Clean up - remove extra newlines and spaces
    linkedin_text = re.sub(r'\n{3,}', '\n\n', linkedin_text)
    linkedin_text = linkedin_text.strip()

    # Add hashtags at the end if they were in the markdown
    hashtags = re.findall(r'#\w+', md_content)
    if hashtags:
        linkedin_text += "\n\n" + " ".join(hashtags)

    return linkedin_text