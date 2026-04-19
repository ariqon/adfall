#!/usr/bin/env python3
"""Uppdaterar databasen med sammanfattningar för refererade domar."""

import sqlite3

# Sammanfattningar för refererade domar
summaries = {
    "AD 2025 nr 2": {
        "parter": "Kärande: Svenska Hamnarbetarförbundet. Svarande: Sveriges Hamnar",
        "sammanfattning": "En fackförening varslade en blockad mot hamnar för att protestera mot transport av krigsmateriell till/från Israel. Frågan var om Arbetsdomstolen kunde bevilja interimistiskt förordnande om att blockaden skulle vara tillåten. Domstolen avslog yrkandet eftersom ingen part utvecklade närmare vilka verkningar blockaden skulle få.",
        "lagrum": "41 § första stycket andra punkten lagen (1976:580) om medbestämmande i arbetslivet",
        "rattsfragor": "Lovligheten av varslade politisk stridsåtgärd (blockad) med internationell bakgrund, villkoren för interimistisk prövning",
        "domslut": "Arbetsdomstolen avslog yrkandet om interimistiskt förordnande"
    },
    "AD 2025 nr 3": {
        "parter": "Kärande: Svenska Hamnarbetarförbundet. Svarande: Sveriges Hamnar",
        "sammanfattning": "Svenska Hamnarbetarförbundet varslade en blockad mot handel med krigsmateriel kopplad till Israel och sökte interimistiskt beslut. Arbetsdomstolen bedömde verkningarna för arbetsgivarnas affärsledningsrätt i relation till kollektivavtalets begränsningar.",
        "lagrum": "Medbestämmandelagen 41 § första stycket andra punkten",
        "rattsfragor": "Interimistisk prövning av rättsliga gränser för politisk stridsåtgärd",
        "domslut": "Arbetsdomstolen biföll förbundets yrkande. Förbundet var rättsligt oförhindrat av sitt kollektivavtal att vidta blockaden."
    },
    "AD 2025 nr 12": {
        "parter": "Kärande: Svenska Polisförbundet. Svarande: Staten genom Polismyndigheten",
        "sammanfattning": "En polisassistent dömdes för nio fall av obefogat dataintrång i Polismyndighetens system över drygt två år. Hon genomförde slagningar efter personuppgifter om sin halvsysters sambo utan arbetsrelaterad anledning, vilket utgjorde hemlig kartläggning av personliga förhållanden.",
        "lagrum": "18 § lagen (1982:80) om anställningsskydd, 2 kap. 6 § andra stycket regeringsformen",
        "rattsfragor": "Huruvida polisassistent kunde avskedas på grund av dataintrång och övervakning utan arbetsliga skäl",
        "domslut": "Arbetsdomstolen fann att avskedandet var befogat. Polisassistenten hade visat sig uppenbarligen olämplig att inneha sin anställning."
    },
    "AD 2025 nr 16": {
        "parter": "Kärande: OFR/S, P, O genom Fackförbundet ST. Svarande: Staten genom Arbetsgivarverket",
        "sammanfattning": "Målet behandlade fastställelse av pensionsålder för tre helikopterpiloter vid Sjöfartsverket. Trots muntlig förberedelse kunde domstolen inte få klarhet i vad käranden yrkade.",
        "lagrum": "4 kap. 6 § lagen (1974:371) om rättegången i arbetstvister",
        "rattsfragor": "Fastställelse av pensionsålder och ekonomiska förmåner under ITP-planen",
        "domslut": "Arbetsdomstolen avvisade fastställelsetalan då kravet inte uppfyllde tröskeln för avsevärd betydelse."
    },
    "AD 2025 nr 17": {
        "parter": "Kärande: Svenska Byggnadsarbetareförbundet. Svarande: Good Folks Sweden AB",
        "sammanfattning": "Tvisten gällde lön och ersättningar för en trafikvakt och om byggavtalet var tillämpligt på arbetet. Parterna var oeniga om vilket kollektivavtal som skulle reglera anställningen.",
        "lagrum": "Kollektivavtalstolkning, 29/29-principen (AD 1929 nr 29)",
        "rattsfragor": "Huruvida byggavtalet är tillämpligt på arbete som trafikvakt",
        "domslut": "Arbetsdomstolen fastställde att byggavtalet inte är tillämpligt på det aktuella arbetet som trafikvakt."
    },
    "AD 2025 nr 23": {
        "parter": "Kärande: A.P. (anställd handläggare). Svarande: Staten genom Försäkringskassan",
        "sammanfattning": "En handläggare vid Försäkringskassan underlät att anmäla ändrade förhållanden i sin egen bostadsbidragsansökan vid upprepade tillfällen, vilket resulterade i felaktig utbetald ersättning och misstanke om bidragsbrott.",
        "lagrum": "Lagen (1982:80) om anställningsskydd 7, 18 och 30 §§, Rättegångsbalken 18 kap. 1 §",
        "rattsfragor": "Laglig grund för avskedande, tvåmånadersfristen, fördelning av rättegångskostnader",
        "domslut": "Avskedandet bedömdes lagligt då handläggarens agerande grovt åsidosatte sina åligganden och skapade allvarlig förtroendeskada."
    },
    "AD 2025 nr 25": {
        "parter": "Kärande: Naturvetarna. Svarande: Malmö kommun",
        "sammanfattning": "En projektledare vid Malmö kommun nekades möjligheten att arbeta som deltidsbrandman vid sidan av sitt ordinarie arbete. Fackföreningen menade att detta strider mot kollektivavtalets regler om bisysslor.",
        "lagrum": "Anställningsskyddslagen 2 b § och 6 §, Arbetsvillkorsdirektivet",
        "rattsfragor": "Huruvida arbetsgivare bryter mot kollektivavtalet genom att neka anställd rätt att utöva bisyssla",
        "domslut": "Se fullständig dom för domslut."
    },
    "AD 2025 nr 29": {
        "parter": "Kärande: Svenska Transportarbetareförbundet. Svarande: Biltrafikens Arbetsgivareförbund och Telepass AB",
        "sammanfattning": "Målet gällde två taxichaufförers rättsliga status när de utförde arbete utöver sin heltidsanställning. Domstolen undersökte om de var anställda direkt hos arbetsgivaren eller hos bemanningsföretaget.",
        "lagrum": "64 § lagen (1976:580) om medbestämmande i arbetslivet",
        "rattsfragor": "Anställningsförhållande vid övertidsarbete, kollektivavtalsbrott, preskription",
        "domslut": "Det var inte bevisat att förarna var anställda hos bemanningsföretaget. Arbetsgivaren bröt mot taxiavtalet genom att inte betala övertidsersättning."
    },
    "AD 2025 nr 35": {
        "parter": "Kärande: Sveriges Hamnar. Svarande: Svenska Hamnarbetarförbundet",
        "sammanfattning": "Efter att Sveriges Hamnar och Svenska Transportarbetareförbundet slutit kollektivavtal för hamnarbetare initierade Svenska Hamnarbetarförbundet egna stridsåtgärder för ett motsvarande avtal. Sveriges Hamnar invände med hänvisning till fredspliktsbestämmelser.",
        "lagrum": "Lagen (1976:580) om medbestämmande i arbetslivet, 41 d och 41 e §§",
        "rattsfragor": "Giltigheten av stridsåtgärder, brott mot fredspliktsreglerna",
        "domslut": "Arbetsdomstolen avvisade Sveriges Hamnars invändningar. Stridsåtgärderna syftade inte till att förtränga befintligt avtal eller utöva otillbörlig påtryckning."
    },
    "AD 2025 nr 39": {
        "parter": "Kärande: Svenska Transportarbetareförbundet. Svarande: Kompetensföretagen",
        "sammanfattning": "Målet avsåg tillämpningen av bemanningsavtalet för arbetare, specifikt hur ersättning ska beräknas för uthyrd personal. Frågan var vilken divisor som ska användas när den uthyrde har timlön men jämförbara grupper hos kunden har månadslön.",
        "lagrum": "Bemanningsavtalet för arbetare",
        "rattsfragor": "Tolkning av bemanningsavtalet gällande divisor för omräkning mellan timlön och månadslön",
        "domslut": "Arbetsdomstolen avslog fastställelseyrkandet. Tillgänglig utredning stödde inte något av de föreslagna divisorerna."
    },
    "AD 2025 nr 44": {
        "parter": "Kärande: Handelsanställdas förbund. Motparter: Föreningen Svensk Handel och Dagab Inköp & Logistik AB",
        "sammanfattning": "Målet avhandlade arbetsgivares förpliktelse att ge skyddsombud tillträde till och inflytande över viktiga organisatoriska förändringar. Centralt var tidpunkten för och omfattningen av skyddsombudens medverkan i besluts- och planeringsprocessen vid försäljning av verksamhetsgren.",
        "lagrum": "Arbetsmiljölagen 6 kap. 4 och 10 §§, Förtroendemannalagen 3 §",
        "rattsfragor": "Skyldighet att ge skyddsombud delaktighet i planering av verksamhetsförsäljning och omorganisation",
        "domslut": "Se fullständig dom för domslut."
    },
    "AD 2025 nr 45": {
        "parter": "Kärande: Sveriges Hamnar. Motpart: Svenska Hamnarbetarförbundet",
        "sammanfattning": "Svenska Hamnarbetarförbundet initierade stridsåtgärder för att uppnå kollektivavtalsbundenhet efter att Sveriges Hamnar tecknat avtal med Svenska Transportarbetareförbundet. Domstolen bedömde att förbundet förhandlat om sina krav och att stridsåtgärderna inte syftade till att tränga undan kollektivavtalet.",
        "lagrum": "Lagen (1976:580) om medbestämmande i arbetslivet, 41 d § och 41 e §",
        "rattsfragor": "Huruvida varslade stridsåtgärder är rättsliga, interimistiskt beslut",
        "domslut": "Sveriges Hamnars invändningar mot stridsåtgärderna förkastades. Begäran om interimistiskt beslut avslogs."
    },
    "AD 2025 nr 47": {
        "parter": "Klagande: AL (anställd plastikkirurg). Motpart: Art Clinic AB",
        "sammanfattning": "En kirurg rapporterade internt om verksamhetsavvikelser, inklusive problem med en narkosläkare. Tvisten handlade om huruvida dessa rapporter skyddades enligt visselblåsarlagen. Domstolen fastställde att bevisningen för vad som utgör missförhållanden av allmänintresse låg på klaganden.",
        "lagrum": "Lagen (2021:890) om skydd för personer som rapporterar om missförhållanden 1 kap. 2 och 8 §§, 3 kap. 5 §",
        "rattsfragor": "Brott mot visselblåsarlagen, missförhållanden av allmänintresse, skadeståndsanspråk baserat på repressalier",
        "domslut": "De rapporterade avvikelserna utgör inte sådana missförhållanden som visselblåsarlagen täcker. Lagskyddet blev inte tillämpligt."
    },
    "AD 2025 nr 50": {
        "parter": "Kärande: Handelsanställdas förbund. Motpart: HAF med enskild firma Frisör House Timrå",
        "sammanfattning": "Domstolen behandlade bevisbördan när arbetsgivare åberopar arbetstagarens skriftliga uppsägning men äktheten ifrågasätts. Specifikt behandlades beviskravet övervägande sannolikt på elektroniska dokument (undertecknade på iPad).",
        "lagrum": "AD 2023 nr 18, NJA 1976 s. 667",
        "rattsfragor": "Bevisbördan för att digitalt undertecknad handling är äkta, tillämpning vid elektroniska dokument",
        "domslut": "Arbetsgivaren bär bevisbördan för att den elektroniska uppsägningshandlingen härrör från arbetstagaren och måste göra detta övervägande sannolikt."
    },
    "AD 2025 nr 53": {
        "parter": "Kärande: Diskrimineringsombudsmannen. Motpart: Emmaboda kommun",
        "sammanfattning": "En biståndshandläggare tilldelades olika ärenden än tidigare efter sin återkomst från föräldraledighet, trots att hennes tidigare uppgifter fortfarande fanns tillgängliga. Ett direkt samband fanns mellan ledighetsperiodens slut och missgynnandet.",
        "lagrum": "16 § föräldraledighetslagen (1995:584), 22 § föräldraledighetslagen",
        "rattsfragor": "Missgynnande efter föräldraledighet, samband mellan ledighet och nya arbetsuppgifter",
        "domslut": "Arbetsdomstolen fastställde att biståndshandläggaren blev missgynnad i strid med föräldraledighetslagen."
    },
    "AD 2025 nr 57": {
        "parter": "Kärande: Sveriges Lärare. Motparter: Burlövs kommun och Varbergs kommun",
        "sammanfattning": "Två gravida lärare förbjöds arbeta under pandemin. De mottog graviditetspenning från Försäkringskassan istället för kommunal lön, vilket innebar lägre ersättning. Domstolen tillämpade EU:s mödraskyddsdirektiv som förbjuder att arbetstagare förlorar inkomsten vid arbetsförbud på grund av graviditet.",
        "lagrum": "Mödraskyddsdirektivet artikel 11.1 (direktiv 92/85/EEG), Arbetsmiljölagen 4 kap. 6 §, Diskrimineringslagen",
        "rattsfragor": "Rätt till bibehållen lön enligt EU:s mödraskyddsdirektiv, diskriminering på grund av kön",
        "domslut": "Kommunerna dömdes att betala lönen till lärarna. Diskriminering baserad på kön fastställdes. Diskrimineringsersättningen reducerades med en tredjedel."
    },
    "AD 2025 nr 68": {
        "parter": "Kärande: AW (formgivare). Motpart: Orrefors Kosta Boda AB",
        "sammanfattning": "AW formgav ljuslyktan Snöbollen på 1970-talet under anställning vid ett glasbruk. Verksamheten överlåts senare till Orrefors Kosta Boda, där AW aldrig varit anställd. AW väckte talan om royalty, men tingsrätten avvisade målet med hänvisning till skiljeklausul.",
        "lagrum": "6 b § anställningsskyddslagen, 2 kap. 7 § andra stycket arbetstvistlagen",
        "rattsfragor": "Huruvida tvist om royaltyersättning utgör arbetstvist, domstols behörighet",
        "domslut": "Tvisten bedömdes inte utgöra en arbetstvist. Varken Arbetsdomstolen eller tingsrätten är behörig domstol."
    },
    "AD 2025 nr 81": {
        "parter": "Kärande: IP (arbetstagarorganisation). Motpart: SERNEKE Bygg AB i konkurs",
        "sammanfattning": "En arbetstagarorganisation assisterade sin medlem med rådgivning i ett förenklat tvistemål vid tingsrätt. Domstolen bedömde vilken påverkan facklig rättshjälp skulle ha på möjligheten att få ersättning för dessa kostnader.",
        "lagrum": "1 kap. 3 d § rättegångsbalken, 18 kap. 8 a § rättegångsbalken",
        "rattsfragor": "Ersättning för rättegångskostnad vid facklig rättshjälp, timkostnad för rättslig rådgivning",
        "domslut": "Medlemmen var berättigad till ersättning för en timmes rättslig rådgivning trots att denna finansierats genom facklig rättshjälp."
    },
    "AD 2025 nr 88": {
        "parter": "Klagande: Livsmedelsarbetareförbundet. Motparter: Livsmedelsföretagen och Scan Sverige AB",
        "sammanfattning": "Tvisten gällde potentiellt brott mot 11 § medbestämmandelagen vid tre tillfällen. Domstolen konstaterade att dotterbolaget inte hade fattat något eget beslut eller agerat för att verkställa moderbolagets beslut gällande aktieförsäljningen.",
        "lagrum": "11 § lagen (1976:580) om medbestämmande i arbetslivet",
        "rattsfragor": "Förhandlingsskyldighet vid moderbolagets försäljning av aktier i dotterbolag",
        "domslut": "Förbundets talan avslogs vad gäller aktieförsäljningen. Övriga tvister avvisades då de inte varit föremål för korrekt genomförda tvisteförhandlingar."
    },
    "AD 2025 nr 91": {
        "parter": "Överklagande part: Skorpion Trans AB",
        "sammanfattning": "Skorpion Trans AB begärde att få ut en ljudinspelning från en arbetstvist. Tingsrätten avslog begäran eftersom ingen inspelning fanns. Domstolen analyserade om begäran grundades på rätten till allmänna handlingar eller på partsinsyn.",
        "lagrum": "6 kap. 8 § offentlighets- och sekretesslagen, 2 kap. 8 § lagen (1974:371) om rättegången i arbetstvister",
        "rattsfragor": "Rätt att få ut ljudinspelning som allmän handling, behörig domstol",
        "domslut": "Begäran avsåg rätten att ta del av allmänna handlingar, inte partsinsyn. Arbetsdomstolen överlämnade målet till hovrätten för prövning."
    },
    "AD 2025 nr 97": {
        "parter": "Kärande: Svenska Hamnarbetarförbundet. Motpart: Sveriges Hamnar och Gothenburg Ro/Ro Terminal AB",
        "sammanfattning": "Domstolen behandlade en konflikt angående preskription av anspråk på ogiltigförklaring av en uppsägning. Det centrala spörsmålet var hur preskriptionsreglerna ska tillämpas när arbetstagare hävdar att uppsägningen kränker föreningsrätten.",
        "lagrum": "Anställningsskyddslagen (1982:80) §§ 40, 42, Medbestämmandelagen (1976:580) §§ 3, 8, 64",
        "rattsfragor": "Preskription vid ogiltigförklaring av uppsägning, förhållandet mellan LAS och MBL vid föreningsrättskränkningar",
        "domslut": "Anställningsskydslagens preskriptionsbestämmelser är speciallag jämfört med medbestämmandelagen. Förhandlingsordnings upphörande utgör utgångspunkt för talefristen."
    },
}

conn = sqlite3.connect('arbetsdomstolen.db')
cursor = conn.cursor()

updated = 0
for malnummer, data in summaries.items():
    cursor.execute('''
        UPDATE domar
        SET parter = ?,
            sammanfattning = ?,
            lagrum = ?,
            rattsfragor = ?,
            domslut = ?
        WHERE malnummer = ?
    ''', (
        data.get('parter', ''),
        data.get('sammanfattning', ''),
        data.get('lagrum', ''),
        data.get('rattsfragor', ''),
        data.get('domslut', ''),
        malnummer
    ))
    if cursor.rowcount > 0:
        updated += 1

conn.commit()
print(f"Uppdaterade {updated} domar med sammanfattningar.")

# Visa en exempeldom
cursor.execute("SELECT * FROM domar WHERE refererad = 1 LIMIT 1")
row = cursor.fetchone()
cols = [d[0] for d in cursor.description]
print("\nExempel på refererad dom:")
for col, val in zip(cols, row):
    if val:
        print(f"  {col}: {val[:100]}..." if isinstance(val, str) and len(val) > 100 else f"  {col}: {val}")

conn.close()
