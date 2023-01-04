import requests
from bs4 import BeautifulSoup
import json
import csv
import sys
import datetime
import time

def writeFile(info, fileName):
    with open(fileName, 'w') as jsonFile:
        jsonFile.write(json.dumps(info))
    print(f"Info saved to {fileName}.")

def readFile(fileName):
    with open(fileName) as jsonFile:
        data = json.load(jsonFile)

        # Print the type of data variable
        print(f'{fileName} loaded as {type(data)}')

        return data
def getTime():
    return datetime.datetime.now()

startW = getTime()
print(f'### INITIALISING AT {startW} ###')
lineNum = 1
writeFile(lineNum, 'bandIDNow.json')

switch = {'Full-length': 'album', 'Single': 'single', 'Demo': 'demo', 'EP': 'other', 'Split': 'other', 'Compilation': 'other', 'Boxed set': 'other'}
flag1 = False
flag2 = False
flag3 = False

def getHTML(url):
    status = 0
    while status != 403:
        page = requests.get(url)
        status = page.status_code
        #print(f"Got a page! {url}")

    #if page.status_code != 403:
    #    print(f'ERROR IN URL: {url}')
    #    sys.exit()
    #time.sleep(2)
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup

def getTracks(albumList, type):
    albumLink = albumList.find_all('a', {'class': switch.get(type, 'other')})
    for album in albumLink:
        link = album['href']
    albumHTML = getHTML(link)
    trackNumList = []
    songList = []
    durationList = []
    lyricsList = []
    tracks = albumHTML.find_all('tr', {'class': ['even', 'odd']})
    for track in tracks:
        trackNumList.append(track.find('td', {'width': '20'}))
        songList.append(track.find('td', {'class': 'wrapWords'}))
        durationList.append(track.find('td', {'align': 'right'}))
        text = track.select('[id^="lyricsButton"]')
        if text == []:
            lyricsList.append('No lyrics found.')
        for text in track.select('[id^="lyricsButton"]'):
            songID = text['href'][1:]
            lyricSoup = getHTML('https://www.metal-archives.com/release/ajax-view-lyrics/id/' + songID)
            lyricsList.append(lyricSoup.text.strip())

    for i in trackNumList:
        if i is None:
            trackNumList[trackNumList.index(i)] = 'None'
    for i in songList:
        if i is None:
            songList[songList.index(i)] = 'None'
    for i in durationList:
        if i is None:
            durationList[durationList.index(i)] = 'None'

    trackNum = []
    song = []
    duration = []
    for num in trackNumList:
        if isinstance(num, str) != True:
            trackNum.append(num.text.strip())
        else:
            trackNum.append(num)
    for s in songList:
        if isinstance(s, str) != True:
            song.append(s.text.strip())
        else:
            song.append(s)
    for d in durationList:
        if isinstance(d, str) != True:
            minSec = d.text.strip().split(':')
            try:
                sec = (int(minSec[0])*60)+int(minSec[1])
            except:
                sec = 0
            duration.append(sec)
        else:
            duration.append(d)

    i = 0
    trackList = []
    while i < len(trackNum):
        trackList.append([trackNum[i][0:1], song[i], duration[i], lyricsList[i]])
        i += 1
    return trackList

def getAlbums(url):
    soup = getHTML(url)
    discoDiv = soup.find_all('div', {'id': 'band_disco'})
    for div in discoDiv:
        links = div.find_all('a', href=True)
        discoLink = []
        for link in links:
            discoLink.append(link['href'])

    albumListHTML = getHTML(discoLink[0]) # complete disco link
    albumList = albumListHTML.find_all('tr')
    albumList = albumList[1:] # remove column row from table
    albums = []

    for album in albumList:
        albumDetails = album.find_all('td')
        if albumDetails[0].text.strip() == "Nothing entered yet. Please add the releases, if applicable.":
            albums.append({'recName': 'None', 'recType': 'None', 'recYear': 'None', 'recTrackList': 'None'})
            return soup, albums
        name = albumDetails[0].text.strip()
        type = albumDetails[1].text.strip()
        year = albumDetails[2].text.strip()
        tracks = getTracks(album, type)

        albums.append({'recName': name, 'recType': type, 'recYear': year, 'recTrackList': tracks})

    return soup, albums

def getArtists(soup):
    artistList = soup.find_all('div', {'id': 'band_tab_members_all'})
    if artistList == []:
        artistList = soup.find_all('div', {'id': 'band_tab_members_current'})
    for artistLink in artistList:
        artistLinks = artistLink.find_all('a', {'class': 'bold'})
        artistRole = artistLink.find_all('td', {'valign': False, 'colspan': False})
        artists = []
        for link in artistLinks:
            artists.append([link.text.strip(), link['href'].split('/')[-1]])
        roles = []
        for role in artistRole:
            roles.append(role.text.strip())
        artistInfo = []
        i = 0
        while i < len(artists):
            artistInfo.append([artists[i][0], artists[i][1], roles[i]])
            i += 1
        return artistInfo

def getBand(url):
    soup, albums = getAlbums(url)
    artists = getArtists(soup)
    bandInfo = soup.find_all('div', {'id': 'band_info'})
    band = []
    for details in bandInfo:
        name = details.find('h1').text.strip()
        detailList = details.find_all('dd')
        country = detailList[0].text.strip()
        city = detailList[1].text.strip()
        status = detailList[2].text.strip()
        formed = detailList[3].text.strip()
        genre = detailList[4].text.strip()
        lyricalThemes = detailList[5].text.strip()

        band.append({'bandName': name, 'bandCountry': country, 'bandCity': city, 'bandStatus': status, 'bandFormed': formed, 'bandGenre': genre, 'bandLyricalThemes': lyricalThemes, 'bandMembers': artists, 'bandRecs': albums})

        return band

def printBandInfo(bandInfo):
    for details in bandInfo:
        print(f'Band Name:\t\t\t\t\t{details["bandName"]}')
        print(f'Band Formed In:\t\t\t\t{details["bandFormed"]}')
        print(f'Band Location:\t\t\t\t{details["bandCity"]}, {details["bandCountry"]}')
        print(f'Band Genre:\t\t\t\t\t{details["bandGenre"]}')
        print(f'Band Lyrical Themes:\t\t{details["bandLyricalThemes"]}')
        print(f'Band Status:\t\t\t\t{details["bandStatus"]}\n')
        for artist in details['bandMembers']:
            print(f'Band Member Name:\t\t\t\t{artist[0]}')
            print(f'Band Member Role:\t\t\t\t{artist[2]}\n')
        for album in details['bandRecs']:
            print(f'Recording Name:\t\t\t\t{album["recName"]}')
            print(f'Recording Type:\t\t\t\t{album["recType"]}')
            print(f'Recording Year:\t\t\t\t{album["recYear"]}\n')
            for track in album['recTrackList']:
                print(f'Track Number:\t\t\t\t{track[0]}\nTrack Name:\t\t\t\t\t{track[1]}\nDuration:\t\t\t\t\t{track[2]} seconds\nLyrics:\n{track[3]}\n')
            for person in album['recPersonnelList']:
                print(f'Recording Personnel Name:\t\t\t{person[0]}\t\t\tRole:\t\t{person[2]}')
            print()

def printBandInfoShort(bandInfo):
    for details in bandInfo:
        print(f'Processed band \"{details["bandName"]}\", {len(details["bandMembers"])} artists, {len(details["bandRecs"])} albums')

with open ('bands_BM.csv', mode= 'r') as file:
    reader = csv.reader(file)
    bandData = list(reader)
    bandDataNew = []
    for band in bandData:
        if band != []:
            bandDataNew.append(band)
    bandData = bandDataNew
    totalLines = len(bandData)-1
    i = 0
    while i < len(bandData):
        i += 1
        #bandData[i] = bandData[i].strip().split(',')

def getBands():
    with open ('bands_BM.csv', mode= 'r') as file:
        csvReadFile = csv.reader(file)
        lineNum = readFile('bandIDNow.json')
        if lineNum == 1:
            flag1 = True
            flag2 = True
            flag3 = True
        else:
            flag1 = False
            flag2 = False
            flag3 = False

        artistNum = 0
        albumNum = 0
        start = getTime()
        print(f'\n\nScraping started at {start}')
        count = 0

        while lineNum < len(bandData):
            #totalPersonnelData = readFile('totalPersonnel.json')
            totalPersonnelData = []
            infoWriteOut = open('1-bandInfo.csv', 'a')
            writerInfo = csv.writer(infoWriteOut)
            if flag1:
                writerInfo.writerow(['id', 'name', 'formedIn', 'city', 'country', 'genre', 'lyricalThemes', 'status', 'memberNames', 'albumNames'])
                flag1 = False

            detailWriteOut = open('2-bandInfoDetail.csv', 'a')
            writerDetail = csv.writer(detailWriteOut)
            if flag2:
                writerDetail.writerow(['id', 'name', 'formedIn', 'city', 'country', 'genre', 'lyricalThemes', 'status', 'albumName', 'albumType', 'albumYear', 'albumTrackNumber', 'albumTrackName', 'albumTrackDuration', 'albumTrackLyrics'])
                flag2 = False

            if bandData[lineNum][0] != 'name':
                print(f'Processing band #{lineNum} out of {totalLines} total')
                id = bandData[lineNum][1].replace(';', '')
                print(f'Current ID:{id}')
                url = 'https://www.metal-archives.com/band/view/id/' + id
                bandInfo = getBand(url)
                #printBandInfo(bandInfo)
                printBandInfoShort(bandInfo)

                for details in bandInfo:
                    artistNum += len(details["bandMembers"])
                    albumNum += len(details["bandRecs"])
                    name = details["bandName"]
                    formed = details["bandFormed"]
                    city = details["bandCity"]
                    country = details["bandCountry"]
                    genre = details["bandGenre"]
                    lyrics = details["bandLyricalThemes"]
                    status = details["bandStatus"]
                    artists = "Members"
                    for artist in details['bandMembers']:
                        artists = ", ".join([artists, artist[0]])

                    albums = "Albums"
                    for album in details['bandRecs']:
                        albums = ", ".join([albums, album['recName']])
                        albumName = album["recName"]
                        if albumName == 'None':
                            break
                        albumType = album["recType"]
                        albumYear = album["recYear"]
                        for track in album['recTrackList']:
                            albumTrackNumber = track[0]
                            albumTrackName = track[1]
                            albumTrackDuration = track[2]
                            albumTrackLyrics = track[3]
                            try:
                                writerDetail.writerow([id, name, formed, city, country, genre, lyrics, status, albumName, albumType, albumYear, albumTrackNumber, albumTrackName, albumTrackDuration, albumTrackLyrics])
                                #print(f'Wrote {albumName}')
                            except:
                                print(f'Failed {albumName}')
                                continue
                try:
                    writerInfo.writerow([id, name, formed, city, country, genre, lyrics, status, artists, albums])
                    print(f'Wrote {name}')
                except:
                    print(f'Failed {name}')
                    pass
                infoWriteOut.close()
                detailWriteOut.close()

                lineNum += 1
                writeFile(lineNum, 'bandIDNow.json')
                count += 1
                #if lineNum == 7:
                #    break

            end = getTime()

            print(f'Scraping finished at {end}.\nProcessed {lineNum-1} bands so far, {artistNum} artists, {albumNum} albums added this run.\nThis iteration lasted (h:mm:ss): {(end-start)}.\n\n')
    return lineNum
lineNum = readFile('bandIDNow.json')

while True:
    if lineNum < totalLines+1:
        lineNum = getBands()
    else:
        break
endW = getTime()
print(f'\n\n\n\n\nTotal process finished at {endW}.\nProcessed {lineNum-1} bands. \nWhole thing lasted (h:mm:ss): {(endW-startW)}.\n\n\n\n\n')