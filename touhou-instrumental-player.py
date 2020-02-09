import random
import os
import requests
import re
import time
import subprocess
import signal
import sys
from bs4 import BeautifulSoup

instrumental = "https://invidio.us/search?q=touhou%20instrumental"
bgm = "https://invidio.us/search?q=touhou+bgm"
classical = "https://invidio.us/search?q=touhou+classical"

def changePage(url, page):
    url = re.sub(r'&page=\d*', '', url)
    url = url + "&page=" + str(page)
    return url

def getUpperBound(session, url, lowerBound):
    url = changePage(url, lowerBound)
    nextUrl = changePage(url, lowerBound+1)
    nextSite = session.get(nextUrl)
    nextSoup = BeautifulSoup(nextSite.text, 'html.parser')
    match = nextSoup.findAll('div', class_='pure-u-1 pure-u-md-1-4')
    if match != []:
        return getUpperBound(session, url, lowerBound*4+1)
    else:
        return lowerBound+1

def getHighestPage(session, url, lowerBound, upperBound):
    print("Getting middle page")
    middlePage = int((lowerBound+upperBound)/2)
    middleUrl = changePage(url, middlePage)
    middleSite = session.get(middleUrl)
    middleSoup = BeautifulSoup(middleSite.text, 'html.parser')
    match = middleSoup.findAll('div', class_='pure-u-1 pure-u-md-1-4')
    if match != []:
        print("Not match")
        nextUrl = changePage(url, middlePage+1)
        nextSite = session.get(nextUrl)
        nextSoup = BeautifulSoup(nextSite.text, 'html.parser')
        match = nextSoup.findAll('div', class_='pure-u-1 pure-u-md-1-4')
        if match != []:
            return getHighestPage(session, url, middlePage+1, upperBound)
        else:
            return middlePage
    else:
        print("Match")
        previousUrl = changePage(url, middlePage-1)
        previousSite = session.get(previousUrl)
        previousSoup = BeautifulSoup(previousSite.text, 'html.parser')
        match = previousSoup.findAll('div', class_='pure-u-1 pure-u-md-1-4')
        if match != []:
            return middlePage-1
        else:
            return getHighestPage(session, url, lowerBound, middlePage-1)

def getListOfHrefs(session, url, page):
    url = changePage(url, page)
    site = session.get(url)
    soup = BeautifulSoup(site.text, 'html.parser')
    temp = soup.findAll('div', class_='pure-u-1 pure-u-md-1-4')
    a = []
    titles = []
    for element in temp:
        a.append((element.find('a')['href'], element.find('p', class_=False).text))
    firstBannedExpression = r"playlist"
    secondBannedExpression = r"vocal|subbed|subs|sub|cover|lyrics|Touhou Sky Arena Matsuri Climax Music Extended|Smooth McGroove"
    listOfHrefs = []
    for element in a:
       firstMatch = re.search(firstBannedExpression, element[0])
       secondMatch = re.search(secondBannedExpression, element[1], re.IGNORECASE)
       if not firstMatch and not secondMatch:
           listOfHrefs.append(element)
    return listOfHrefs

def getListOfVideos(listOfHrefs):
    listOfVideos = []
    for element in listOfHrefs:
        listOfVideos.append(("https://youtube.com" + element[0], element[1]))
    return listOfVideos

def interrupt(signum, frame):
    raise Exception("")

def getChoice(prompt):
    choice = ""
    timeout = 20
    #signal.alarm(timeout)
    signal.signal(signal.SIGALRM, interrupt)
    signal.alarm(timeout) # sets timeout
    while(True):
        try:
            choice = input(prompt)
        except:
            return choice
        if choice == "1" or choice == "2" or choice == "3" or choice == "Q":
            signal.alarm(0)
            return choice

links = [instrumental, bgm, classical]
mainTheme = random.randint(0,2) 

def score(title):
    score = 0
    f = open(sys.argv[1], "r")
    for line in f:
        line_divided = line.split(',', maxsplit=1)
        line_score = int(line_divided[0])
        line_text = line_divided[1][:-1] #remove the trailing \n
        match = re.search(line_text, title, re.IGNORECASE)
        if match:
            score+=line_score
    f.close()
    return score

def getFilterInput(message, title):
    while True:
        user_input = input(message)
        match = re.search(r".*\,.*\d", user_input)
        if not match and user_input != "A":
            print("Wrongly formatted input, try again.\n")
            continue
        if user_input == "A":
            user_input = title
            user_score = input("Enter the score: ")
            try:
                int(user_score)
            except ValueError:
                print("Wrongly formatted score, try again.\n")
                continue
            user_input = re.sub('\|\||\&\&|\&|\|', '', user_input)
            return str(user_score)  + ',' + user_input + '\n'
        return user_input + '\n'

def addFilter(title):
    f = open(sys.argv[1], "a")
    message = "Enter the filter, separated by a , from the score. Negative score needs - prefix; eg. niggy, -50. Escape commas with '\\'. To add the entire title to filters, enter 'A'\n"
    f.write(getFilterInput(message, title))
    

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'})

print("Getting upper bound page...")
upperBound = getUpperBound(session, instrumental, 1)
print("Getting highest page...")
highestPage = getHighestPage(session, links[mainTheme], upperBound/4-1, upperBound)
print("Getting random page...")
randomPage = random.randint(1,highestPage)
print("Getting list of videos...")
listOfVideos = getListOfVideos(getListOfHrefs(session, links[mainTheme], randomPage))
while True:
    print("Entering loop")
    for element in listOfVideos:
        print(element)
        if len(sys.argv) > 1:
            points = score(element[1])
            print("Points: " + str(points))
            if points <= 0:
                print("Points below or equal zero, skipping")
                continue
        print("Setting title")
        title = element[1]
        print("Setting address")
        address = element[0]
        print(title)
        print(address)
        if len(sys.argv) > 1:
            print("Touhou-ness score: " + str(points))
        subprocess.call(["mpv", "--no-video", "--af=scaletempo=speed=both", "--audio-pitch-correction=no", "--ytdl-format=bestaudio", element[0]])
        choice = getChoice("Press 1 to download the file, press 2 to go to the next, press 3 to add a new filter, press Q to quit.\n")
        if choice == "1":
            subprocess.call(["youtube-dl", "-x", "-o", "'%(title)s.%(ext)s'", "--audio-quality", "0", "--audio-format", "flac", element[0]])
        elif choice == "2":
            pass
        elif choice == "3":
            addFilter(title)
        elif choice == "Q":
            sys.exit()
        else:
            pass
    randomPage = random.randint(1, int(highestPage))
    listOfVideos = getListOfVideos(getListOfHrefs(session, links[mainTheme], randomPage))
        









