import random
import os
import requests
import re
import time
import subprocess
import signal
from bs4 import BeautifulSoup

instrumental = "https://invidio.us/search?q=touhou%20instrumental"
bgm = "https://invidio.us/search?q=touhou+bgm"

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
    middlePage = int((lowerBound+upperBound)/2)
    middleUrl = changePage(url, middlePage)
    middleSite = session.get(middleUrl)
    middleSoup = BeautifulSoup(middleSite.text, 'html.parser')
    match = middleSoup.findAll('div', class_='pure-u-1 pure-u-md-1-4')
    if match != []:
        nextUrl = changePage(url, middlePage+1)
        nextSite = session.get(nextUrl)
        nextSoup = BeautifulSoup(nextSite.text, 'html.parser')
        match = nextSoup.findAll('div', class_='pure-u-1 pure-u-md-1-4')
        if match != []:
            return getHighestPage(session, url, middlePage+1, upperBound)
        else:
            return middlePage
    else:
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
    secondBannedExpression = r"vocal|subbed|subs|sub|cover"
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
        if choice == "1" or choice == "2":
            signal.alarm(0)
            return choice

links = [instrumental, bgm]
mainTheme = random.randint(0,1) 

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'})

upperBound = getUpperBound(session, instrumental, 1)
highestPage = getHighestPage(session, links[mainTheme], upperBound/4-1, upperBound)
randomPage = random.randint(1,highestPage)
listOfVideos = getListOfVideos(getListOfHrefs(session, links[mainTheme], randomPage))
while True:
    for element in listOfVideos:
        print(element[1])
        print(element[0])
        subprocess.call(["mpv", "--no-video", "--af=scaletempo=speed=both", "--audio-pitch-correction=no", "--ytdl-format=bestaudio", element[0]])
        choice = getChoice("Press 1 to download the file, press 2 to go to the next.\n")
        if choice == "1":
            subprocess.call(["youtube-dl", "-x", "-o", "'%(title)s.%(ext)s'", "--audio-quality", "0", "--audio-format", "flac", element[0]])
        elif choice == "2":
            pass
        else:
            pass
    randomPage = random.randint(1, int(highestPage))
    listOfVideos = getListOfVideos(getListOfHrefs(session, links[mainTheme], randomPage))
        









