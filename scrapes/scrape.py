import requests
from bs4 import BeautifulSoup
from re import compile as _re_compile
import json
from time import sleep as _time_sleep

### Constants ###

base_url = "https://www.ted.com"

talks_url = base_url + "/talks?"

page_key = "page"

sort_key = "sort"
sort_value = "popular"
    # Sorting by views so that whatever I get first is at least relevant to an 'ideal' talk

transcript_url_extension = "/transcript.json?language=en"
    # transcript json can be found at base_url + '/TALK_ID' + extension


### Scrape links to talks ###
def scrape_links(num_pages=81, outfile=None):
    '''
    Scrapes the links to TED talks from the Browse page.
    Returns list of links (relative url assumes base_url www.ted.com)
    Optional number of pages to scrape and file (should be a csv) to output.
    '''

    talk_links = []

    # There are 81 pages
    for current_page in range(num_pages):

        # Load results page
        page_html = requests.get(talks_url, params={page_key:current_page + 1, sort_key:sort_value}).text
        soup = BeautifulSoup(page_html, "html.parser")

        talks = soup.find(id="browse-results").find_all("a", class_="ga-link")[1::2]
            # The page has a link in the image and a link in the title, I only need one.
            # I'm choosing the second of the two since the image link has children which are irrelevant.

        # Append just the href to the list of links
        for talk in talks:
            talk_links.append(talk["href"])

        if (current_page + 1) % 10 == 0:
            print("Scraped", len(talk_links), "LINKS so far, taking a little break.")
            _time_sleep(60)

    if outfile:
        with open(outfile, 'w') as file:
            file.write(link + ", " for link in talk_links)

    return talk_links

#! Can only scrape 9 at full speed before the following response:
    # '429 Rate Limited too many requests.'
    #
    # Probably can add a time.sleep for (?) seconds every ninth talk

### Scrape individual talks ###
def scrape_talks(talk_links, outfile, skippedfile, start_at=0):
    '''
    Scrapes the talk pages for a TED talk, getting information and the
    transcript tokenized by cue cards.
    Returns nothing.
    Takes list of talk links, filepath to output of scrapes, and filepath to
    output of skipped talks.
    '''

    for index, talk_link in enumerate(talk_links):

        # Allow for starting part way through the list in case of exception
        if index < start_at:
            continue

        ### Get information about the talk ###
        
        talk_res = requests.get(base_url + talk_link)
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

        # If multiple speakers, a performance, or grabbed from the web (no transcript) just skip to next talk
        if (len(talk["speakers"]) > 1) or ("performance" in talk["tags"]) or (talk["video_type"]["id"] == '5'):
            # Log talk name and primary speaker so I can check to make sure I'm not
            # skipping something that I shouldn't!
            print("Skipping", talk["title"])
            with open(skippedfile, 'a', encoding="utf-8") as file:
                file.write(str((talk["title"], talk["id"], talk["speaker_name"], talk_link)) + '\n')

            # Remember to sleep
            if (index + 1) % 5 == 0:
                print("Scraped", index + 1, "TALKS so far, taking a little break.")
                _time_sleep(60)

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

        try:
            # Get list of paragraphs from transcript
            for paragraph in transcript_json["paragraphs"]:
                # Each paragraph contains a list of cue sets
                for cue in paragraph["cues"]:
                    # Append text from cue to our set of token
                    tokens.append(cue["text"])

            data["tokens"] = tokens
        except KeyError:
            print("Skipping", talk["title"])
            with open(skippedfile, 'a', encoding="utf-8") as file:
                file.write(str((talk["title"], talk["id"], talk["speaker_name"], talk_link)) + '\n')

            # Remember to sleep
            if (index + 1) % 5 == 0:
                print("Scraped", index + 1, "TALKS so far, taking a little break.")
                _time_sleep(60)

            continue

        # Debug print
        print("Just scraped \"", data["title"], "\" Now writing.")


        ### Append data of this talk to file ###

        # Opening and appending to file each time to preserve memory and allow
            # for thrown exceptions to not destroy progress!

        # Every line of this file will contains a dictionary object of the talk

        with open(outfile, 'a', encoding="utf-8") as talk_file:
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
            # besides simply a longer sleep.
            #
            # Next day, decided that it doesn't matter if I just leave this scrape
            # running, I can wait between scrapes no worries.

        if (index + 1) % 5 == 0:
            print("Scraped", index + 1, "TALKS so far, taking a little break.")
            _time_sleep(60)
        
def get_talk_links_from_file(filepath):

    talk_links = []

    with open(filepath, 'r') as file:
        data = file.read()
        # Split by comma separator, the last item has a following comma so we
        # can ignore the '' last result.
        talk_links = data.split(", ")[:-1]

    return talk_links
