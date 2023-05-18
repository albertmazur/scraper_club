import requests
from bs4 import BeautifulSoup

def getSoup(url):
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    return BeautifulSoup(response.text, 'html.parser')

domain = "https://www.transfermarkt.pl"
url = "https://www.transfermarkt.pl/wettbewerbe/europa"

plik = open("dane_klubu.txt", "w", encoding="utf-8")
plikCypher = open("database.cypher", "w", encoding="utf-8")

def getTrophist(url, who):
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
        for sezon in sesonTexts.split(", "):
            print('MATCH (n {nazwa:"'+who+'"}) CREATE (t:Trofeum {nazwa:"'+nameTrohy+'"}), (n)-[r:wygrali {sezon:"'+sezon+'"}]->(t) RETURN n, r, t;')

        plik.write(nameTrohy+" | "+sesonTexts+"\n")

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
            plik.write(str(currentNation)+" | "+nameNation+"\n")
            print('CREATE (k:Kraj {nazwa:"' + nameNation + '"}) RETURN k;')

            getTrophist(url, nameNation)
            # print("Pobrano narodowości:"+str(round((currentNation/210)*100, 2))+"%")


getNationality()

def getCouch(url):
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
    plik.write(name+" | "+wiek+" | "+narodowosc+" | "+od+" | "+do.strip()+"\n")


def getPlayers(url):
    soup = getSoup(url)

    # Pobranie informacji o stadionie
    divStadium = soup.find("div", {"class": "data-header__info-box"})
    ulStadium = divStadium.find_all("ul")
    liStadium = ulStadium[-1].find_all("li")

    nameStadium = liStadium[1].find("a").text
    setStadium = liStadium[1].find("span", {"class": "tabellenplatz"}).text

    #print(nameStadium+" | "+setStadium)
    plik.write(nameStadium+" | "+setStadium + "\n")

    # Pobranie trenera z kontraktem
    getCouch(url)

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
        plik.write(str(i+1)+" | "+name+" | "+position+" | "+dateBirth+" | "+nation+" | "+odContract+" | "+doContract+" | "+walue+"\n")

    tropyLink = soup.find("div", {'class', 'data-header__badge-container'})
    tropyLink = tropyLink.find("a")
    if tropyLink is not None:
        url = tropyLink.get('href')
        getTrophist(domain + url)


def getClubs(url):
    soup = getSoup(url)

    table = soup.find('table', {'class': 'items'})
    trs = table.find_all('tr', class_=['odd', 'even'])

    for i, tr in enumerate(trs):
        td = tr.find("td", {'class': 'hauptlink'})
        a = td.find("a")

        #print(str(i+1)+" | "+a.get("title")+" | "+domain+a.get("href"))
        plik.write(str(i+1)+" | "+a.get("title")+" | "+domain+a.get("href")+"\n")

        getPlayers(domain+a.get("href"))


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

    #print(str(i+1)+" | "+a.get("title")+" | "+img.get("title")+" | "+countClub+" | "+domain + a.get('href'))
    plik.write(str(i+1)+" | "+a.get("title")+" | "+img.get("title")+" | "+countClub+" | "+domain + a.get('href')+"\n")

    getClubs(domain + a.get('href'))
    print("Pobrano ligi w raz z klubami:" + str(round(((i+1) / len(trs)) * 100, 2)) + "%")

plikCypher.close()
plik.close()