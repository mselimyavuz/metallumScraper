import requests
from bs4 import BeautifulSoup
import json
import csv
import sys
import datetime

switch = {'Full-length': 'album', 'Single': 'single', 'Demo': 'demo', 'EP': 'other', 'Split': 'other', 'Compilation': 'other', 'Boxed set': 'other'}
totalPersonnelData = []

def getTime():
    return datetime.datetime.now()

def writeFile(info, fileName):
    with open(fileName, 'w') as jsonFile:
        jsonFile.write(json.dumps(info))
    print(f"Info saved to {fileName}.")

def readFile(fileName):
    with open(fileName) as jsonFile:
        data = json.load(jsonFile)

        # Print the type of data variable
        print(f'File loaded as {type(data)}')

        return data

def getHTML(url):
    page = requests.get(url)
    if page.status_code != 403:
        print(f'ERROR IN URL: {url}')
        sys.exit()
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup

def genreList():
    genres = {}
    url = 'https://www.metal-archives.com/browse/genre'
    soup = getHTML(url)
    genreLinksDiv = soup.find('div', {'id': 'content_wrapper'})
    genreLinks = genreLinksDiv.find_all('a')
    for link in genreLinks[:-1]: # no need for the advanced search link
        genres[link.text] = link['href']
    return genres

def getPersonnelDetail(url):
    id = url.split('/')[-1]
    soup = getHTML(url)
    cols = soup.find_all('dt')
    values = soup.find_all('dd')
    bands = soup.find_all('div', {'class': 'member_in_band'})
    bandRoles = {}
    for band in bands:
        bandName = band.find('h3')
        roles = band.select('[id^="memberInAlbum"]')
        roleInBand = []
        for role in roles:
            album = role.find('a', {'href': True})
            specificRole = role.find('td', {'width': False})
            roleInBand.append([album.text.strip(), specificRole.text.strip()])
        bandRoles[bandName.text.strip()] = roleInBand
    personnelDict = {}
    i = 0
    while i < len(cols):
        personnelDict[cols[i].text.strip()] = values[i].text.strip()
        personnelDict['Bands'] = bandRoles
        personnelDict['id'] = id
        i += 1
    return personnelDict

def getAlbumPersonnel(soup):
    personnelDiv = soup.find_all('div', {'id': 'album_all_members_lineup'})
    if personnelDiv == []:
        personnelDiv = soup.find_all('div', {'id': 'album_members_lineup'})
    personnelList = []
    for personnel in personnelDiv:
        lineup = personnel.find_all('tr', {'class': 'lineupRow'})
        for person in lineup:
            member = person.find('a', {'href': True})
            role = person.find('td', {'valign': False})
            personnelData = getPersonnelDetail(member['href'])
            totalPersonnelData.append(personnelData)
            personnelList.append([member.text.strip(), member['href'].split('/')[-1], role.text.strip()])
    return personnelList

def getTracks(albumList, type):
    albumLink = albumList.find_all('a', {'class': switch.get(type, 'other')})
    for album in albumLink:
        link = album['href']
    albumHTML = getHTML(link)
    personnel = getAlbumPersonnel(albumHTML)
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
    return personnel, trackList

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
        name = albumDetails[0].text.strip()
        type = albumDetails[1].text.strip()
        year = albumDetails[2].text.strip()
        personnel, tracks = getTracks(album, type)

        albums.append({'recName': name, 'recType': type, 'recYear': year, 'recTrackList': tracks, 'recPersonnelList': personnel})

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
with open ('bands.csv', mode= 'r') as file:
    reader = csv.reader(file)
    data = list(reader)
    totalLines = len(data)

infoWriteOut = open('bandInfo.csv', 'w')
writerInfo = csv.writer(infoWriteOut)
writerInfo.writerow(['id', 'name', 'formedIn', 'city', 'country', 'genre', 'lyricalThemes', 'status', 'memberNames', 'albumNames'])

detailWriteOut = open('bandInfoDetail.csv', 'w')
writerDetail = csv.writer(detailWriteOut)
writerDetail.writerow(['id', 'name', 'formedIn', 'city', 'country', 'genre', 'lyricalThemes', 'status', 'memberName', 'memberID', 'memberRole', 'albumName', 'albumType', 'albumYear', 'albumTrackNumber', 'albumTrackName', 'albumTrackDuration', 'albumTrackLyrics'])

artistWriteOut = open('artistInfo.csv', 'w')
artistDetail = csv.writer(artistWriteOut)
artistDetail.writerow(['id', 'name', 'placeOfBirth', 'gender', 'age', 'band', 'album', 'role'])

with open ('bands.csv', mode= 'r') as file:
    csvReadFile = csv.reader(file)
    lineNum = 1
    artistNum = 0
    albumNum = 0
    start = getTime()
    print(f'Scraping started at {start}')
    for line in csvReadFile:
        if line[0] != 'name':
            print(f'Processing band #{lineNum} out of {totalLines} total')
            id = line[1].replace(';', '')
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
                    albumType = album["recType"]
                    albumYear = album["recYear"]
                    for track in album['recTrackList']:
                        albumTrackNumber = track[0]
                        albumTrackName = track[1]
                        albumTrackDuration = track[2]
                        albumTrackLyrics = track[3]
                        for person in album['recPersonnelList']:
                            memberName = person[0]
                            memberID = person[1]
                            memberRole = person[2]
                            writerDetail.writerow([id, name, formed, city, country, genre, lyrics, status, memberName, memberID, memberRole, albumName, albumType, albumYear, albumTrackNumber, albumTrackName, albumTrackDuration, albumTrackLyrics])
            writerInfo.writerow([id, name, formed, city, country, genre, lyrics, status, artists, albums])


            lineNum += 1
        #if lineNum == 2:
        #    break

    for person in totalPersonnelData:
        for band in person['Bands'].keys():
            for role in person['Bands'][band]:
                artistDetail.writerow([person['id'], person['Real/full name:'], person['Place of birth:'], person['Gender:'], person['Age:'], band, role[0], role[1]])

    infoWriteOut.close()
    detailWriteOut.close()
    artistWriteOut.close()
    end = getTime()
    #print(totalPersonnelData)
    print(f'Scraping finished at {end}.\nProcessed {lineNum} bands, {artistNum} artists, {albumNum} albums.\nThis lasted (h:mm:ss): {(end-start)}.')
