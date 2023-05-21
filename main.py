import requests
from bs4 import BeautifulSoup

def getSoup(url):
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    return BeautifulSoup(response.text, 'html.parser')

domain = "https://www.transfermarkt.pl"
url = "https://www.transfermarkt.pl/wettbewerbe/europa"

plikCypher = open("database.cypher", "w", encoding="utf-8")

def getTrophist(url, who, clubOrNation):
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')

    divs = soup.find_all("div", {"class": "erfolg_bild_box"})
    for div in divs:
        mainDiv = div.parent
        divName = mainDiv.find("div", {"class", "erfolg_bild_box"})
        img = divName.find("img")

        divSeson = mainDiv.find("div", {"class", "erfolg_infotext_box"})
        sesonTexts = ''.join(divSeson.text.split())
        sesonTexts = sesonTexts.replace(",", ", ")

        #print(img.get("title")+" | "+sesonTexts)
        nameTrohy = img.get("title")
        beginQuery = 'MATCH (k:' + clubOrNation + ' {nazwa:"' + who + '"}) MERGE (t:Trofeum {nazwa:"' + nameTrohy + '"}) CREATE'
        relationQuery = ""
        endQuery = ""
        sezons = sesonTexts.split(", ")
        for i, sezon in enumerate(sezons):
            if len(sezons) != i+1: relationQuery = relationQuery+'(k)-[r'+str(i)+':wygrali {sezon:"'+sezon+'"}]->(t), '
            else : relationQuery = relationQuery+'(k)-[r'+str(i)+':wygrali {sezon:"'+sezon+'"}]->(t) '
            endQuery = endQuery+"r"+str(i)+", "

            #print('MATCH (k:'+clubOrNation+' {nazwa:"'+who+'"}) MERGE (t:Trofeum {nazwa:"'+nameTrohy+'"}) MERGE (k)-[r:wygrali {sezon:"'+sezon+'"}]->(t) RETURN k, r, t;')
        plikCypher.write(beginQuery+relationQuery+"RETURN "+endQuery+"k, t;\n")

def getNationality():
    for page in range(1, 10):
        soup = getSoup(domain + "/" + "wettbewerbe/fifa?ajax=yw1&page="+str(page))
        table = soup.find('table', {'class': 'items'})
        trs = table.find_all('tr', class_=['odd', 'even'])

        for i, tr in enumerate(trs):
            a = tr.find("a")
            aUrl = a.get("href")
            czesci = aUrl.split('/')
            url = domain + '/' + czesci[1] + '/' + "erfolge/verein/" + czesci[4]
            currentNation = (i+1)+((page-1)*25)
            nameNation = a.get("title")

            #print(str(currentNation)+" | "+nameNation+"\n")

            plikCypher.write('CREATE (k:Kraj {nazwa:"' + nameNation + '"}) RETURN k;\n')

            getTrophist(url, nameNation, "Kraj")
            print("Pobrano narodowości: "+str(round((currentNation/210)*100, 2))+"%")

getNationality()

def getCouch(url, nameClub):
    czesci = url.split('/')
    url = domain+'/'+czesci[3]+'/'+"mitarbeiter/verein/"+czesci[6]

    soup = getSoup(url)

    table = soup.find("table")
    tbody = table.find("tbody")
    tr = tbody.find("tr")
    tdName = tr.find("td")
    tds = tr.find_all("td", {"class": "zentriert"})

    name = tdName.find("a").text

    wiek = tds[0].text

    img = tds[1].find("img")
    narodowosc = img.get("title")

    od = tds[2].text
    do = tds[3].text

    #print(name+" | "+wiek+" | "+narodowosc+" | "+od+" | "+do.strip())
    plikCypher.write('CREATE (t:Trener {imie_i_nazwisko:"'+name+'", wiek:"'+wiek+'"}) WITH t MATCH (k:Kraj {nazwa:"'+narodowosc+'"}), (c:Klub {nazwa:"'+nameClub+'"}) CREATE (t)-[r1:pochodzi]->(k), (t)-[r2:kontrakt {od_kiedy:"'+od+'", do_kiedy:"'+do.strip()+'"}]->(c) RETURN t, k, c, r1, r2;\n')

def getPlayers(url, nameClub):
    soup = getSoup(url)

    # Pobranie informacji o stadionie
    divStadium = soup.find("div", {"class": "data-header__info-box"})
    ulStadium = divStadium.find_all("ul")
    liStadium = ulStadium[-1].find_all("li")

    nameStadium = liStadium[1].find("a").text
    setStadium = liStadium[1].find("span", {"class": "tabellenplatz"}).text

    setStadium = setStadium.replace(" miejsc", "")
    #print(nameStadium+" | "+setStadium)

    plikCypher.write('CREATE (s:Stadion {nazwa:"'+nameStadium+'", miejsca:"'+setStadium+'"}) WITH s MATCH (c:Klub {nazwa:"'+nameClub+'"}) CREATE (s)-[r:nalezy]->(c) RETURN s, r, c;\n')
    # Pobranie trenera z kontraktem
    getCouch(url, nameClub)

    # Pobranie szczegółowej listy zawodników
    divTabs = soup.find("div", {"class", "tm-tabs"})
    links = divTabs.find_all("a")
    url = domain+links[1].get("href")
    soup = getSoup(url)

    table = soup.find('table', {'class': 'items'})
    trs = table.find_all('tr', class_=['odd', 'even'])

    for i, tr in enumerate(trs):
        # Imię, nazwisko i pozycja
        table = tr.find("table", {'class': 'inline-table'})
        trName = table.find_all("tr")
        tdName = trName[0].find("td", {'class': 'hauptlink'})
        name = tdName.find("a").text.strip()
        position = trName[1].find("td").text.strip()

        tds = tr.find_all("td", {'class': 'zentriert'})
        # Data urodzenia
        dateBirth = tds[1].text[:-5]
        # Narodowość
        nation = tds[2].find("img").get("title")

        odContract = tds[5].text
        doContract = tds[7].text

        # Wartość rynkowa
        walue = tr.find("td", {'class': 'rechts'}).text

        #print(str(i+1)+" | "+name+" | "+position+" | "+dateBirth+" | "+nation+" | "+odContract+" | "+doContract+" | "+walue)
        plikCypher.write('CREATE (z:Zawodnik {imie_i_nazwisko:"'+name+'", pozycja:"'+position+'", data_urodzenia:"'+dateBirth+'"}) MATCH (k:Kraj {nazwa:"'+nation+'"}) MATCH (c:Klub {nazwa:"'+nameClub+'"}) CREATE (z)-[r1:nalezy]->(k), (z)-[r2:kontrakt {od_kiedy:"'+odContract+'", do_kiedy:"'+doContract+'",wartosc:"'+walue+'"}]->(c) RETURN z, c, k, r1, r2;\n')

    tropyLink = soup.find("div", {'class', 'data-header__badge-container'})
    tropyLink = tropyLink.find("a")
    if tropyLink is not None:
        url = tropyLink.get('href')
        getTrophist(domain + url, nameClub, "Klub")


def getClubs(url, country, nameLig):
    soup = getSoup(url)

    table = soup.find('table', {'class': 'items'})
    trs = table.find_all('tr', class_=['odd', 'even'])

    for i, tr in enumerate(trs):
        td = tr.find("td", {'class': 'hauptlink'})
        a = td.find("a")

        nameClub = a.get("title")
        #print(str(i+1)+" | "+nameClub+" | "+domain+a.get("href"))
        plikCypher.write('CREATE (k:Klub {nazwa:"'+nameClub+'"}) MATCH (t:Kraj {nazwa:"'+country+'"}) CREATE (k)-[r:nalezy {nazwa:"'+nameLig+'"}]->(t) RETURN k, r, t;\n')
        getPlayers(domain+a.get("href"), nameClub)


soup = getSoup(url)
tableLig = soup.find('table', {'class': 'items'})
trs = tableLig.find_all('tr', class_=['odd', 'even'])

for i, tr in enumerate(trs):
    table = tr.find("table", {'class': 'inline-table'})
    tds = table.find_all("td")
    td = tds[1]
    a = td.find("a")

    td2 = tr.find_all("td", {'class': 'zentriert'})
    img = td2[0].find("img")

    countClub = td2[1].text
    country = img.get("title")
    nameLig = a.get("title")

    #print(str(i+1)+" | "+nameLig+" | "+country+" | "+countClub+" | "+domain + a.get('href'))

    getClubs(domain + a.get('href'), country, nameLig)
    print("Pobrano ligi w raz z klubami: " + str(round(((i+1) / len(trs)) * 100, 2)) + "%")

plikCypher.close()