# ted-talks-analysis

Some exploratory data analysis of TED talk transcripts.  I thought of this project so that I could work on work on:
- Webscraping
- Simple text analysis
- NLTK library for Python
- Principle component analysis
- Data visualization and interactivity
- LSTM neural net to generate original text from a corpus

---

Gameplan:
- Scrape all (currently 2888) English transcripts of TED talks
- Included data:
  - Title (and talk ID)
  - Speaker (and speaker ID)
  - \# of views on TED
  - \# of comments on TED 
  - date published
  - TED tags (topics)
  - original language (specific word usage will be skewed by translation)
  - video length (to calculate rough wpm)
  - Event (e.g. TEDx vs TED Global)
- Run some basic analysis (duration, length, common words, past/future tense, passive/active voice, etc)
- Break into categories (perhaps popularity) and try to use PCA to find the specific distinguishing words
- Feed text into LSTM and churn out a sudo TED talk
- Create a nice interactive visalization of results
