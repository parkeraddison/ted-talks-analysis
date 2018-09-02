import requests
from bs4 import BeautifulSoup
import re
import json

base_url = "https://www.ted.com"

talks_url = base_url + "/talks?"

page_key = "page"

sort_key = "sort"
sort_value = "popular"
    # Sorting by views so that whatever I get first is at least relevant to an 'ideal' talk

transcript_url_extension = "/transcript.json?language=en"
    # transcript json can be found at base_url + '/TALK_ID' + extension

# How many talks to scrape
SCRAPE_AMOUNT = 1

# Start at page 1
current_page = 1

# Load results page
page_html = requests.get(talks_url, params={page_key:current_page, sort_key:sort_value}).text
soup = BeautifulSoup(page_html, "html.parser")

talks = soup.find(id="browse-results").find_all("a", class_="ga-link")[1::2]
    # The page has a link in the image and a link in the title, I only need one.
    # I'm choosing the second of the two since the image link has children which are irrelevant.


# TODO: In the future I'll add support to scrape links from multiple pages

for i in range(SCRAPE_AMOUNT):

    ### Get information about the talk ###
    
    talk_page_html = requests.get(base_url + talks[i]["href"]).text
    talk_soup = BeautifulSoup(talk_page_html, "html.parser")

    # Scrape <script> that contains ' "__INITIAL_DATA__" object
        # Maybe I should scrape using javascript... this should already be loaded in as an object
        # ...
        # Just tested, web console showed _q as empty, couldn't locate INITIAL object.
        # _q and q() are being used by an external script with the use of eval.
        # Stick with Python here.
    script = talk_soup.find("script", string=re.compile("__INITIAL_DATA__"))

    # Getting html after object declaration and removing newline and outer object close
    talk_data_string = script.text.split('"__INITIAL_DATA__":')[1][:-3]

    talk_data = json.loads(talk_data_string)
    talk = talk_data["talks"][0]

    data = {}

    data["name"] = talk["title"]
    data["talk_id"] = talk["id"]
    # Possibly need to handle multiple speakers

    # speakers = []
    # for j in range(len(talk_data["speakers"])):
    #     speaker = talk_data["speakers"][j]
    #     speaker_info = {speaker["id"]: speaker["firstname"] + speaker["lastname"]}
    #     speakers.append(speaker_info)
    # data["speakers"] = speakers
    data["speaker"] = talk["speaker_name"]
    data["speaker_id"] = talk["speakers"][0]["id"]
    data["num_views"] = talk["viewed_count"]
    data["num_comments"] = talk_data["comments"]["count"]
    data["date"] = talk["recorded_at"]
    data["tags"] = talk["tags"]
    data["categories"] = talk["ratings"]
    data["language"] = talk_data["language"]
    data["duration"] = talk["duration"]
    data["event"] = talk_data["event"]


    ### Get the transcript ###

    # I have two options here, I could request the transcript from the page itself,
        # which handles parsing the json that stores the transcript, and I could
        # very easily scrape the <p> tags with attribute "dir" : "ltr".
        # 
        # Or I can request just the json and parse it myself.
        #
        # Scraping the page would be much simpler, but I think parsing would be
        # fast for scraping purposes.

    # The splitting of the transcript into cues may be useful for tokenization.
        # I'll store the text as a list of the cue text.  I can always concat
        # then tokenize again if I want.
    transcript_json = requests.get(base_url + "/talks/" + data["talk_id"] + transcript_url_extension).json()

    tokens = []

    # Get list of paragraphs from transcript
    for paragraph in transcript_json["paragraphs"]:
        # Each paragraph contains a list of cue sets
        for cue in paragraph["cues"]:
            # Append text from cue to our set of token
            tokens.append(cue["text"])

    data["tokens"] = tokens


    ### Append data of this talk to file ###

    # Every line of this file will contain a json object of a talk.

    with open("ted_talks.txt", 'a') as talk_file:
        talk_file.write(str(data) + '\n')
