import requests
from bs4 import BeautifulSoup
from re import compile as _re_compile
import json
from time import sleep as _time_sleep

base_url = "https://www.ted.com"

talks_url = base_url + "/talks?"

page_key = "page"

sort_key = "sort"
sort_value = "popular"
    # Sorting by views so that whatever I get first is at least relevant to an 'ideal' talk

transcript_url_extension = "/transcript.json?language=en"
    # transcript json can be found at base_url + '/TALK_ID' + extension

# Start at page 1
current_page = 1

# Load results page
page_html = requests.get(talks_url, params={page_key:current_page, sort_key:sort_value}).text
soup = BeautifulSoup(page_html, "html.parser")

talks = soup.find(id="browse-results").find_all("a", class_="ga-link")[1::2]
    # The page has a link in the image and a link in the title, I only need one.
    # I'm choosing the second of the two since the image link has children which are irrelevant.

# TODO: In the future I'll add support to scrape links from multiple pages


#! Can only scrape 9 at full speed before the following response:
    # '429 Rate Limited too many requests.'
    #
    # Probably can add a time.sleep for (?) seconds every ninth talk


# List of skipped talks (performances or interviews)
skipped = []

for i in range(36):

    ### Get information about the talk ###
    
    talk_res = requests.get(base_url + talks[i]["href"])
    talk_page_html = talk_res.text
    talk_soup = BeautifulSoup(talk_page_html, "html.parser")

    # Scrape <script> that contains ' "__INITIAL_DATA__" object
        # Maybe I should scrape using javascript... this should already be loaded in as an object
        # ...
        # Just tested, web console showed _q as empty, couldn't locate INITIAL object.
        # _q and q() are being used by an external script with the use of eval.
        # Stick with Python here.
    script = talk_soup.find("script", string=_re_compile("__INITIAL_DATA__"))

    # Getting html after object declaration and removing newline and outer object close
    talk_data_string = script.text.split("\"__INITIAL_DATA__\":")[1][:-3]

    talk_data = json.loads(talk_data_string)
    talk = talk_data["talks"][0]

    # If multiple speakers/performance/interview, just skip to next talk
    if (len(talk["speakers"]) > 1) or ("performance" in talk["tags"]):
        # Log talk name and primary speaker so I can check to make sure I'm not
        # skipping something that I shouldn't!
        skipped.append(talk["title"], talk["id"], talk["speaker_name"])
        continue

    # Add talk information
    data = {}
    data["title"] = talk["title"]
    data["talk_id"] = talk["id"]
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
    transc_res = requests.get(base_url + "/talks/" + data["talk_id"] + transcript_url_extension)
    transcript_json = transc_res.json()

    tokens = []

    # Get list of paragraphs from transcript
    for paragraph in transcript_json["paragraphs"]:
        # Each paragraph contains a list of cue sets
        for cue in paragraph["cues"]:
            # Append text from cue to our set of token
            tokens.append(cue["text"])

    data["tokens"] = tokens


    # Debug print
    print("Just scraped \"", data["title"], "\" Now writing.")


    ### Append data of this talk to file ###

    # Every line of this file will contain a json object of a talk.

    with open("./ted_talks.txt", 'a') as talk_file:
        talk_file.write(str(data) + '\n')

    # Debug
    print("Written.")

    ### Add some rest after every fifth scrape ###
        # As mentioned above, too many requests leads to a rate limit
        #
        # Ran into issue with transcript this time, need to wait longer.
        #
        # Previously paused every ninth, more frequent now to hopefully avoid
        #
        # Still didn't work. Ran into a stricter limit this time (7). Response
        # does not have headers that reveal the limit!  Looking into solutions
        # besides simply a longer sleep...

    if (i + 1) % 5 == 0:
        _time_sleep(5)


for talk in skipped:
    print(talk)