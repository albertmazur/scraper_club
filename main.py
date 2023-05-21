import requests
from bs4 import BeautifulSoup
from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
password = "P@$$w0rd"
driver = GraphDatabase.driver(uri, auth=("neo4j", password))
plikCypher = open("database.cypher", "w", encoding="utf-8")
def add_dataCountry(tx, nameNation):
    tx.run("CREATE (k:Kraj {nazwa:$nameNation}) RETURN k", nameNation=nameNation)
    plikCypher.write('CREATE (k:Kraj {nazwa:"' + nameNation + '"}) RETURN k;\n')

def add_dataPlayer(tx, name, position, dateBirth, nation, nameClub, odContract, doContract, walue):
    tx.run("MATCH (k:Kraj {nazwa:$nation}), (c:Klub {nazwa:$nameClub}) CREATE (z:Zawodnik {imie_i_nazwisko:$name, pozycja:$position, data_urodzenia:$dateBirth}), (z)-[r1:pochodzi]->(k), (z)-[r2:kontrakt {od_kiedy:$odContract, do_kiedy:$doContract, wartosc:$walue}]->(c) RETURN z, c, k, r1, r2", name=name, position=position, dateBirth=dateBirth, nation=nation, nameClub=nameClub, odContract=odContract, doContract=doContract, walue=walue)
    plikCypher.write('MATCH (k:Kraj {nazwa:"'+nation+'"}), (c:Klub {nazwa:"'+nameClub+'"}) CREATE (z:Zawodnik {imie_i_nazwisko:"'+name+'", pozycja:"'+position+'", data_urodzenia:"'+dateBirth+'"}), (z)-[r1:pochodzi]->(k), (z)-[r2:kontrakt {od_kiedy:"'+odContract+'", do_kiedy:"'+doContract+'",wartosc:"'+walue+'"}]->(c) RETURN z, c, k, r1, r2;\n')

def add_dataCouch(tx, name, wiek, narodowosc, nameClub, od, do):
    tx.run("MATCH (k:Kraj {nazwa:$narodowosc}), (c:Klub {nazwa:$nameClub}) CREATE (t:Trener {imie_i_nazwisko:$name, wiek:$wiek}), (t)-[r1:pochodzi]->(k), (t)-[r2:kontrakt {od_kiedy:$od, do_kiedy:$do}]->(c) RETURN t, k, c, r1, r2", name=name, wiek=wiek, narodowosc=narodowosc, nameClub=nameClub, od=od, do=do)
    plikCypher.write('MATCH (k:Kraj {nazwa:"' + narodowosc + '"}), (c:Klub {nazwa:"' + nameClub + '"}) CREATE (t:Trener {imie_i_nazwisko:"' + name + '", wiek:"' + wiek + '"}), (t)-[r1:pochodzi]->(k), (t)-[r2:kontrakt {od_kiedy:"' + od + '", do_kiedy:"' + do.strip() + '"}]->(c) RETURN t, k, c, r1, r2;\n')

def add_dataStadium(tx, nameStadium, setStadium, nameClub):
    tx.run("MATCH (c:Klub {nazwa:$nameClub}) CREATE (s:Stadion {nazwa:$nameStadium, miejsca:$setStadium}), (s)-[r:nalezy]->(c) RETURN s, r, c", nameStadium=nameStadium, setStadium=setStadium, nameClub=nameClub)
    plikCypher.write('MATCH (c:Klub {nazwa:"' + nameClub + '"}) CREATE (s:Stadion {nazwa:"' + nameStadium + '", miejsca:"' + setStadium + '"}), (s)-[r:nalezy]->(c) RETURN s, r, c;\n')

def add_dataClub(tx, nameClub, country, nameLig):
    tx.run("MATCH (t:Kraj {nazwa:$country}) CREATE (k:Klub {nazwa:$nameClub}), (k)-[r:nalezy {nazwa:$nameLig}]->(t) RETURN k, r, t;", nameClub=nameClub, country=country, nameLig=nameLig)
    plikCypher.write('MATCH (t:Kraj {nazwa:"' + country + '"}) CREATE (k:Klub {nazwa:"' + nameClub + '"}), (k)-[r:nalezy {nazwa:"' + nameLig + '"}]->(t) RETURN k, r, t;\n')

def add_dataTrophist(tx, clubOrNation, who, nameTrohy, sezon):
    tx.run("MATCH (k:"+clubOrNation+" {nazwa:$who}) MERGE (t:Trofeum {nazwa:$nameTrohy}) CREATE (k)-[r:wygrali {sezon:$sezon}]->(t) RETURN k, r, t", who=who, nameTrohy=nameTrohy, sezon=sezon)
    plikCypher.write('MATCH (k:' + clubOrNation + ' {nazwa:"' + who + '"}) MERGE (t:Trofeum {nazwa:"' + nameTrohy + '"}) CREATE (k)-[r:wygrali {sezon:"' + sezon + '"}]->(t) RETURN k, r, t;\n')

def getSoup(url):
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    return BeautifulSoup(response.text, 'html.parser')

domain = "https://www.transfermarkt.pl"
url = "https://www.transfermarkt.pl/wettbewerbe/europa"

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

        nameTrohy = img.get("title")
        sezons = sesonTexts.split(", ")

        for i, sezon in enumerate(sezons):
            with driver.session() as session: session.execute_write(add_dataTrophist, clubOrNation, who, nameTrohy, sezon)

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

            with driver.session() as session: session.execute_write(add_dataCountry, nameNation)

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

    with driver.session() as session: session.execute_write(add_dataCouch, name, wiek, narodowosc, nameClub, od, do.strip())
def getPlayers(url, nameClub):
    soup = getSoup(url)

    # Pobranie informacji o stadionie
    divStadium = soup.find("div", {"class": "data-header__info-box"})
    ulStadium = divStadium.find_all("ul")
    liStadium = ulStadium[-1].find_all("li")

    nameStadium = liStadium[1].find("a").text
    setStadium = liStadium[1].find("span", {"class": "tabellenplatz"}).text

    setStadium = setStadium.replace(" miejsc", "")

    with driver.session() as session: session.execute_write(add_dataStadium, nameStadium, setStadium, nameClub)

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

        with driver.session() as session: session.execute_write(add_dataPlayer, name, position, dateBirth, nation, nameClub, odContract, doContract, walue)

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

        with driver.session() as session: session.execute_write(add_dataClub, nameClub, country, nameLig)

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

    getClubs(domain + a.get('href'), country, nameLig)
    print("Pobrano ligi w raz z klubami: " + str(round(((i+1) / len(trs)) * 100, 2)) + "%")

plikCypher.close()
driver.close()