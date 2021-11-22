#!/usr/local/bin/python3
# pip install webdriver-manager
import os
from os.path import join, dirname
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient
from interruptingcow import timeout
import json

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
client = MongoClient(os.environ.get("DB_URI"))

def getSubjectArea():
    dict = {}
    s = Service(ChromeDriverManager().install())
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options, service=s)
    driver.get('https://registrar.ucla.edu/academics/course-descriptions')

    driver.implicitly_wait(10)
    links = driver.find_elements_by_css_selector(
        'div.course-descriptions-letter > ol > li > a')
    for link in links:
        dict[link.text] = link.get_attribute('href')
    driver.close()
    return dict

def getSubjectName(url):
    s = Service(ChromeDriverManager().install())
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options, service=s)
    driver.get(url)
    name = None
    while (True):
        name = driver.find_element_by_css_selector('#block-ucla-sa-page-title > h1').text
        if (name != 'Course Descriptions'):
            break
    res = name.split(" (")
    res[1] = res[1][:-1]
    driver.close()
    return res

def getSubjectAreas():
    dict = {}
    s = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s)
    driver.get('https://catalog.registrar.ucla.edu/')
    driver.implicitly_wait(10)
    driver.find_element_by_css_selector(
        'ul.react-tabs__tab-list.css-1yjrdhj-TabContainer--StyledTabList.e1798nnl0 > li:nth-of-type(3)').click()
    driver.implicitly_wait(10)
    links = driver.find_elements_by_css_selector(
        'ul.css-9prh2s-TilesGrid--STileList.e1rfl7qt0 > li > a')
    for link in links:
        dict[link.find_element_by_css_selector('h4').text] = link.get_attribute('href')
    driver.close()
    return dict

def getClasses(url, subject):
    x = len(url.split("/")[-1])
    s = Service(ChromeDriverManager().install())
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options, service=s)
    s = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s)
    # Using this one as an example
    driver.get(url)
    driver.implicitly_wait(20)
    # https://stackoverflow.com/questions/743164/how-to-emulate-a-do-while-loop
    # Check curr page first before advancing to next page
    do = True
    dict = {}
    count = 0
    try:
        with timeout(10.0, exception=RuntimeError):
            print("Waiting for timeout")
            while (do):
                with timeout(8.0, exception=RuntimeError):
                    try:
                        driver.implicitly_wait(50)
                        links = driver.find_elements_by_css_selector(
                            'a.cs-list-item.css-1hhgbew-Links--StyledLink-Links--StyledAILink.e1t6s54p8')
                        
                        for link in links:
                            try:
                                
                                shortName = subject + " " + (link.get_attribute('href').split('/')[-1][x:])
                                if (shortName in dict):
                                    count += 1
                                    if count >= 200:
                                        do = False
                                    break
                                dict[shortName] = link.find_element_by_css_selector('div > div.unit-title').text
                            except:
                                break
                            # print(link.find_element_by_css_selector(
                            #     'div > div:nth-of-type(4)').text)
                        # next = driver.find_element_by_css_selector(
                        #     'button#pagination-page-next')
                        # next_class = next.get_attribute('class').split()
                        # https://code.luasoftware.com/tutorials/selenium/selenium-check-element-has-class/
                        # do = not '.css-10i1zya-Button--Button-Button-Button--IconButton-IconButton-Pagination--SPButton:disabled' in next_class
                        driver.execute_script(
                            "document.getElementById('pagination-page-next').click()")
                    except:
                        do = False
                        continue
    except RuntimeError:
        print("Timeout reached")
        driver.close() 
        return dict
    driver.close()  
    return dict

def composeSOCUrl(data):
    links = []
    for key in data:
        longName = key.replace(' ', '+')
        shortName = data[key][1].replace(' ', '+')
        print(longName, shortName)
        links.append("https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName={longName}+{shortName}&t=21W&sBy=subject&subj={shortName}&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex".format(longName=longName, shortName=shortName))
    return links


def uploadAllClassesToDB():
    client = MongoClient(os.environ.get("DB_URI"))
    db = client["onTrackDB"]
    collection = db["AllCourses"]
    allCourses = []
    with open('classdump3.json') as json_file:
        data = json.load(json_file)
        for list in data:
            for prop in list:
                allCourses.append({'Short name': prop, 'Full name:': list[prop]})
    # allCourses = list(set(allCourses))
    with open('classdump2.json') as json_file:
        data = json.load(json_file)
        for list in data:
            for prop in list:
                allCourses.append({'Short name': prop, 'Full name:': list[prop]})
    # allCourses = list(set(allCourses))
    with open('classdump.json') as json_file:
        data = json.load(json_file)
        for list in data:
            for prop in list:
                allCourses.append({'Short name': prop, 'Full name:': list[prop]})
    # uniqueCourseList = {frozenset(item.items()) : item for item in allCourses}.values()
    # print(uniqueCourseList)
    collection.insert_one({"courses": allCourses});

# Main

# subjects = getSubjectArea()
# for key, value in subjects.items():
#     subjects[key] = getSubjectName(value)

# print(subjects)
# catalogSubjects = getSubjectAreas()

data = {'Aerospace Studies': ['Aerospace Studies', 'AERO ST'], 'African American Studies': ['African American Studies', 'AF AMER'], 'African Studies': ['African Studies', 'AFRC ST'], 'American Indian Studies': ['American Indian Studies', 'AM IND'], 'American Sign Language': ['American Sign Language', 'ASL'], 'Ancient Near East': ['Ancient Near East', 'AN N EA'], 'Anesthesiology': ['Anesthesiology', 'ANES'], 'Anthropology': ['Anthropology', 'ANTHRO'], 'Applied Linguistics': ['Applied Linguistics', 'APPLING'], 'Arabic': ['Arabic', 'ARABIC'], 'Archaeology': ['Archaeology', 'ARCHEOL'], 'Architecture and Urban Design': ['Architecture and Urban Design', 'ARCH&UD'], 'Armenian': ['Armenian', 'ARMENIA'], 'Art': ['Art', 'ART'], 'Art History': ['Art History', 'ART HIS'], 'Arts and Architecture': ['Arts and Architecture', 'ART&ARC'], 'Arts Education': ['Arts Education', 'ARTS ED'], 'Asian': ['Asian', 'ASIAN'], 'Asian American Studies': ['Asian American Studies', 'ASIA AM'], 'Astronomy': ['Astronomy', 'ASTR'], 'Atmospheric and Oceanic Sciences': ['Atmospheric and Oceanic Sciences', 'A&O SCI'], 'Bioengineering': ['Bioengineering', 'BIOENGR'], 'Bioinformatics (Graduate)': ['Bioinformatics', 'Graduate', 'BIOINFO)'], 'Bioinformatics (Undergraduate)': ['Bioinformatics', 'Undergraduate', 'BIOINFR)'], 'Biological Chemistry': ['Biological Chemistry', 'BIOL CH'], 'Biomathematics': ['Biomathematics', 'BIOMATH'], 'Biomedical Research': ['Biomedical Research', 'BMD RES'], 'Biostatistics': ['Biostatistics', 'BIOSTAT'], 'Bulgarian': ['Bulgarian', 'BULGR'], 'Central and East European Studies': ['Central and East European Studies', 'C&EE ST'], 'Chemical Engineering': ['Chemical Engineering', 'CH ENGR'], 'Chemistry and Biochemistry': ['Chemistry and Biochemistry', 'CHEM'], 'Chicana/o and Central American Studies': ['Chicana/o and Central American Studies', 'CCAS'], 'Chinese': ['Chinese', 'CHIN'], 'Civil and Environmental Engineering': ['Civil and Environmental Engineering', 'C&EE'], 'Classics': ['Classics', 'CLASSIC'], 'Clusters': ['Clusters', 'CLUSTER'], 'Communication': ['Communication', 'COMM'], 'Community Engagement and Social Change': ['Community Engagement and Social Change', 'CESC'], 'Community Health Sciences': ['Community Health Sciences', 'COM HLT'], 'Comparative Literature': ['Comparative Literature', 'COM LIT'], 'Computational and Systems Biology': ['Computational and Systems Biology', 'C&S BIO'], 'Computer Science': ['Computer Science', 'COM SCI'], 'Conservation of Cultural Heritage': ['Conservation of Cultural Heritage', 'CLT HTG'], 'Czech': ['Czech', 'CZCH'], 'Dance': ['Dance', 'DANCE'], 'Dentistry': ['Dentistry', 'DENT'], 'Design / Media Arts': ['Design / Media Arts', 'DESMA'], 'Digital Humanities': ['Digital Humanities', 'DGT HUM'], 'Disability Studies': ['Disability Studies', 'DIS STD'], 'Dutch': ['Dutch', 'DUTCH'], 'Earth, Planetary, and Space Sciences': ['Earth, Planetary, and Space Sciences', 'EPS SCI'], 'East Asian Studies': ['East Asian Studies', 'EA STDS'], 'Ecology and Evolutionary Biology': ['Ecology and Evolutionary Biology', 'EE BIOL'], 'Economics': ['Economics', 'ECON'], 'Education': ['Education', 'EDUC'], 'Electrical and Computer Engineering': ['Electrical and Computer Engineering', 'EC ENGR'], 'Engineering': ['Engineering', 'ENGR'], 'English': ['English', 'ENGL'], 'English as A Second Language': ['English as A Second Language', 'ESL'], 'English Composition': ['English Composition', 'ENGCOMP'], 'Environment': ['Environment', 'ENVIRON'], 'Environmental Health Sciences': ['Environmental Health Sciences', 'ENV HLT'],'Epidemiology': ['Epidemiology', 'EPIDEM'], 'Ethnomusicology': ['Ethnomusicology', 'ETHNMUS'], 'European Languages and Transcultural Studies': ['European Languages and Transcultural Studies', 'ELTS'], 'Family Medicine': ['Family Medicine', 'FAM MED'], 'Filipino': ['Filipino', 'FILIPNO'], 'Film and Television': ['Film and Television', 'FILM TV'], 'Food Studies': ['Food Studies', 'FOOD ST'], 'French': ['French', 'FRNCH'], 'Gender Studies': ['Gender Studies', 'GENDER'], 'Geography': ['Geography', 'GEOG'], 'German': ['German', 'GERMAN'], 'Gerontology': ['Gerontology', 'GRNTLGY'], 'Global Health': ['Global Health', 'GLB HLT'], 'Global Jazz Studies': ['Global Jazz Studies', 'GJ STDS'], 'Global Studies': ['Global Studies', 'GLBL ST'], 'Graduate Student Professional Development': ['Graduate Student Professional Development', 'GRAD PD'], 'Greek': ['Greek', 'GREEK'], 'Health Policy and Management': ['Health Policy and Management', 'HLT POL'], 'Healthcare Administration': ['Healthcare Administration', 'HLT ADM'], 'Hebrew': ['Hebrew', 'HEBREW'], 'Hindi-Urdu': ['Hindi-Urdu', 'HIN-URD'], 'History': ['History', 'HIST'], 'Honors Collegium': ['Honors Collegium', 'HNRS'], 'Human Genetics': ['Human Genetics', 'HUM GEN'], 'Hungarian': ['Hungarian', 'HNGAR'], 'Indigenous Languages of the Americas': ['Indigenous Languages of the Americas', 'IL AMER'], 'Indo-European Studies': ['Indo-European Studies', 'I E STD'], 'Indonesian': ['Indonesian', 'INDO'], 'Information Studies': ['Information Studies', 'INF STD'], 'International and Area Studies': ['International and Area Studies', 'I A STD'], 'International Development Studies': ['International Development Studies', 'INTL DV'], 'International Migration Studies': ['International Migration Studies', 'I M STD'], 'Iranian': ['Iranian', 'IRANIAN'], 'Islamic Studies': ['Islamic Studies', 'ISLM ST'], 'Italian': ['Italian', 'ITALIAN'], 'Japanese': ['Japanese', 'JAPAN'], 'Jewish Studies': ['Jewish Studies', 'JEWISH'], 'Korean': ['Korean', 'KOREA'], 'Labor Studies': ['Labor Studies', 'LBR STD'], 'Latin': ['Latin', 'LATIN'], 'Latin American Studies': ['Latin American Studies', 'LATN AM'], 'Law': ['Law', 'LAW'], 'Law (Undergraduate)': ['Law', 'Undergraduate', 'UG-LAW)'], 'Lesbian, Gay, Bisexual, Transgender, and Queer Studies': ['Lesbian, Gay, Bisexual, Transgender, and Queer Studies', 'LGBTQS'], 'Life Sciences': ['Life Sciences', 'LIFESCI'], 'Linguistics': ['Linguistics', 'LING'], 'Lithuanian': ['Lithuanian', 'LTHUAN'], 'Management': ['Management', 'MGMT'], 'Management-Executive MBA': ['Management-Executive MBA', 'MGMTEX'], 'Management-Full-Time MBA': ['Management-Full-Time MBA', 'MGMTFT'], 'Management-Fully Employed MBA': ['Management-Fully Employed MBA', 'MGMTFE'], 'Management-Global Executive MBA Asia Pacific': ['Management-Global Executive MBA Asia Pacific', 'MGMTGEX'], 'Management-Master of Financial Engineering': ['Management-Master of Financial Engineering', 'MGMTMFE'], 'Management-Master of Science in Business Analytics': ['Management-Master of Science in Business Analytics', 'MGMTMSA'], 'Management-PhD': ['Management-PhD', 'MGMTPHD'], 'Materials Science and Engineering': ['Materials Science and Engineering', 'MAT SCI'], 'Mathematics': ['Mathematics', 'MATH'], 'Mechanical and Aerospace Engineering': ['Mechanical and Aerospace Engineering', 'MECH&AE'], 'Medical History': ['Medical History', 'MED HIS'], 'Medicine': ['Medicine', 'MED'], 'Microbiology, Immunology, and Molecular Genetics': ['Microbiology, Immunology, and Molecular Genetics', 'MIMG'], 'Middle Eastern Studies': ['Middle Eastern Studies', 'M E STD'], 'Military Science': ['Military Science', 'MIL SCI'], 'Molecular and Medical Pharmacology': ['Molecular and Medical Pharmacology', 'M PHARM'], 'Molecular Biology': ['Molecular Biology', 'MOL BIO'], 'Molecular Toxicology': ['Molecular Toxicology', 'MOL TOX'], 'Molecular, Cell, and Developmental Biology': ['Molecular, Cell, and Developmental Biology', 'MCD BIO'], 'Molecular, Cellular, and Integrative Physiology': ['Molecular, Cellular, and Integrative Physiology', 'MC&IP'], 'Music': ['Music', 'MUSC'], 'Music Industry': ['Music Industry', 'MSC IND'], 'Musicology': ['Musicology', 'MUSCLG'], 'Naval Science': ['Naval Science', 'NAV SCI'], 'Near Eastern Languages': ['Near Eastern Languages', 'NR EAST'], 'Neurobiology': ['Neurobiology', 'NEURBIO'], 'Neurology': ['Neurology', 'NEURLGY'], 'Neuroscience': ['Neuroscience', 'NEUROSC'], 'Neuroscience (Graduate)': ['Neuroscience', 'Graduate', 'NEURO)'], 'Neurosurgery': ['Neurosurgery', 'NEURSGY'], 'Nursing': ['Nursing', 'NURSING'], 'Obstetrics and Gynecology': ['Obstetrics and Gynecology', 'OBGYN'], 'Ophthalmology': ['Ophthalmology', 'OPTH'], 'Oral Biology': ['Oral Biology', 'ORL BIO'], 'Orthopaedic Surgery': ['Orthopaedic Surgery', 'ORTHPDC'], 'Pathology and Laboratory Medicine': ['Pathology and Laboratory Medicine', 'PATH'], 'Pediatrics': ['Pediatrics', 'PEDS'], 'Philosophy': ['Philosophy', 'PHILOS'], 'Physics': ['Physics', 'PHYSICS'], 'Physics and Biology in Medicine': ['Physics and Biology in Medicine', 'PBMED'], 'Physiological Science': ['Physiological Science', 'PHYSCI'], 'Physiology': ['Physiology', 'PHYSIOL'], 'Polish': ['Polish', 'POLSH'], 'Political Science': ['Political Science', 'POL SCI'], 'Portuguese': ['Portuguese', 'PORTGSE'], 'Program in Computing': ['Program in Computing', 'COMPTNG'], 'Psychiatry and Biobehavioral Sciences': ['Psychiatry and Biobehavioral Sciences', 'PSYCTRY'], 'Psychology': ['Psychology', 'PSYCH'], 'Public Affairs': ['Public Affairs', 'PUB AFF'], 'Public Health': ['Public Health', 'PUB HLT'], 'Public Policy': ['Public Policy', 'PUB PLC'], 'Radiation Oncology': ['Radiation Oncology', 'RAD ONC'], 'Religion, Study of': ['Religion, Study of', 'RELIGN'], 'Romanian': ['Romanian', 'ROMANIA'], 'Russian': ['Russian', 'RUSSN'], 'Scandinavian': ['Scandinavian', 'SCAND'], 'Science Education': ['Science Education', 'SCI EDU'], 'Semitic': ['Semitic', 'SEMITIC'], 'Serbian/Croatian': ['Serbian/Croatian', 'SRB CRO'], 'Slavic': ['Slavic', 'SLAVC'], 'Social Science': ['Social Science', 'SOC SC'], 'Social Thought': ['Social Thought', 'SOC THT'], 'Social Welfare': ['Social Welfare', 'SOC WLF'], 'Society and Genetics': ['Society and Genetics', 'SOC GEN'], 'Sociology': ['Sociology', 'SOCIOL'], 'South Asian': ['South Asian', 'S ASIAN'], 'Southeast Asian': ['Southeast Asian', 'SEASIAN'], 'Spanish': ['Spanish', 'SPAN'], 'Statistics': ['Statistics', 'STATS'], 'Surgery': ['Surgery', 'SURGERY'], 'Swahili': ['Swahili', 'SWAHILI'], 'Thai': ['Thai', 'THAI'], 'Theater': ['Theater', 'THEATER'], 'Turkic Languages': ['Turkic Languages', 'TURKIC'], 'Ukrainian': ['Ukrainian', 'UKRN'], 'University Studies': ['University Studies', 'UNIV ST'], 'Urban Planning': ['Urban Planning', 'URBN PL'], 'Urology': ['Urology', 'UROLOGY'], 'Vietnamese': ['Vietnamese', 'VIETMSE'], 'World Arts and Cultures': ['World Arts and Cultures', 'WL ARTS'], 'Yiddish': ['Yiddish', 'YIDDSH']}

catalogSubjects = {'Aerospace Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/AEROST', 'African American Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/AFAMER', 'African Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/AFRCST', 'American Indian Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/AMIND', 'American Sign Language': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ASL', 'Ancient Near East': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ANNEA', 'Anesthesiology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ANES', 'Anthropology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ANTHRO', 'Applied Linguistics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/APPLING', 'Arabic': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARABIC', 'Archaeology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARCHEOL', 'Architecture and Urban Design': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARCHUD', 'Armenian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARMENIA', 'Art': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ART', 'Art History': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARTHIS', 'Arts Education': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARTSED', 'Arts and Architecture': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARTARC', 'Asian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ASIAN', 'Asian American Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ASIAAM', 'Astronomy': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ASTR', 'Atmospheric and Oceanic Sciences': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/AOSCI', 'Bioengineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOENGR', 'Bioinformatics, Graduate': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOINFO', 'Bioinformatics, Undergraduate': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOINFR', 'Biological Chemistry': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOLCH', 'Biomathematics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOMATH', 'Biomedical Research': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BMDRES', 'Biostatistics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOSTAT', 'Bulgarian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BULGR', 'Central and East European Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CEEST', 'Chemical Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CHENGR', 'Chemistry and Biochemistry': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CHEM', 'Chicana/o and Central American Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CCAS', 'Chinese': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CHIN', 'Civil and Environmental Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CEE', 'Classics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CLASSIC', 'Clusters': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CLUSTER', 'Communication': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/COMM', 'Community Engagement and Social Change': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CESC', 'Community Health Sciences': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/COMHLT', 'Comparative Literature': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/COMLIT', 'Computational and Systems Biology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CSBIO', 'Computer Science': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/COMSCI', 'Conservation of Cultural Heritage': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CLTHTG', 'Czech': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CZCH', 'Dance': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/DANCE', 'Dentistry': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/DENT', 'Design|Media Arts': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/DESMA', 'Digital Humanities': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/DGTHUM', 'Disability Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/DISSTD', 'Dutch': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/DUTCH', 'Earth, Planetary, and Space Sciences': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/EPSSCI', 'East Asian Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/EASTDS', 'Ecology and Evolutionary Biology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/EEBIOL', 'Economics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ECON', 'Education': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/EDUC', 'Electrical and Computer Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ECENGR', 'Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ENGR', 'English': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ENGL', 'English Composition': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ENGCOMP', 'English as a Second Language': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ESL', 'Environment': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ENVIRON', 'Environmental Health Sciences': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ENVHLT', 'Epidemiology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/EPIDEM', 'Ethnomusicology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ETHNMUS', 'European Languages and Transcultural Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ELTS', 'Family Medicine': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/FAMMED', 'Filipino': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/FILIPNO', 'Film and Television': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/FILMTV', 'Food Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/FOODST', 'French': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/FRNCH', 'Gender Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GENDER', 'Geography': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GEOG', 'German': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GERMAN', 'Gerontology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GRNTLGY', 'Global Health': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GLBHLT', 'Global Jazz Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GJSTDS', 'Global Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GLBLST', 'Graduate Student Professional Development': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GRADPD', 'Greek': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GREEK', 'Health Policy and Management': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HLTPOL', 'Healthcare Administration': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HLTADM', 'Hebrew': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HEBREW', 'Hindi-Urdu': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HINURD', 'History': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HIST', 'Honors Collegium': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HNRS', 'Human Genetics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HUMGEN', 'Hungarian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HNGAR', 'Indigenous Languages of the Americas': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ILAMER', 'Indo-European Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/IESTD', 'Indonesian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/INDO', 'Information Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/INFSTD', 'International Development Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/INTLDV', 'International Migration Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/IMSTD', 'International and Area Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/IASTD', 'Iranian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/IRANIAN', 'Islamic Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ISLMST', 'Italian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ITALIAN', 'Japanese': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/JAPAN', 'Jewish Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/JEWISH', 'Korean': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/KOREA', 'Labor Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LBRSTD', 'Latin': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LATIN', 'Latin American Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LATNAM', 'Law, Undergraduate': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/UGLAW', 'Lesbian, Gay, Bisexual, Transgender, and Queer Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LGBTQS', 'Life Sciences': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LIFESCI', 'Linguistics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LING', 'Lithuanian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LTHUAN', 'Management': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMT', 'Management-Executive MBA': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTEX', 'Management-Full-Time MBA': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTFT', 'Management-Fully Employed MBA': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTFE', 'Management-Global Executive MBA Asia Pacific': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTGEX', 'Management-Master of Financial Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTMFE', 'Management-Master of Science in Business Analytics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTMSA', 'Management-PhD': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTPHD', 'Materials Science and Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MATSCI', 'Mathematics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MATH', 'Mechanical and Aerospace Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MECHAE', 'Medical History': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MEDHIS', 'Medicine': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MED', 'Microbiology, Immunology, and Molecular Genetics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MIMG', 'Middle Eastern Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MESTD', 'Military Science': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MILSCI', 'Molecular Biology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MOLBIO', 'Molecular Toxicology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MOLTOX', 'Molecular and Medical Pharmacology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MPHARM', 'Molecular, Cell, and Developmental Biology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MCDBIO', 'Molecular, Cellular, and Integrative Physiology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MCIP', 'Music': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MUSC', 'Music Industry': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MSCIND', 'Musicology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MUSCLG', 'Naval Science': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NAVSCI', 'Near Eastern Languages': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NREAST', 'Neurobiology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NEURBIO', 'Neurology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NEURLGY', 'Neuroscience, Graduate': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NEURO', 'Neuroscience, Undergraduate': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NEUROSC', 'Neurosurgery': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NEURSGY', 'Nursing': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NURSING', 'Obstetrics and Gynecology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/OBGYN', 'Ophthalmology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/OPTH', 'Oral Biology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ORLBIO', 'Orthopaedic Surgery': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ORTHPDC', 'Pathology and Laboratory Medicine': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PATH', 'Pediatrics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PEDS', 'Philosophy': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PHILOS', 'Physics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PHYSICS', 'Physics and Biology in Medicine': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PBMED', 'Physiological Science': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PHYSCI', 'Physiology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PHYSIOL', 'Polish': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/POLSH', 'Political Science': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/POLSCI', 'Portuguese': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PORTGSE', 'Program in Computing': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/COMPTNG', 'Psychiatry and Biobehavioral Sciences': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PSYCTRY', 'Psychology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PSYCH', 'Public Affairs': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PUBAFF', 'Public Health': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PUBHLT', 'Public Policy': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PUBPLC', 'Radiation Oncology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/RADONC', 'Religion, Study of': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/RELIGN', 'Romanian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ROMANIA', 'Russian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/RUSSN', 'Scandinavian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SCAND', 'Science Education': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SCIEDU', 'Semitic': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SEMITIC', 'Serbian/Croatian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SRBCRO', 'Slavic': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SLAVC', 'Social Science': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SOCSC', 'Social Thought': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SOCTHT', 'Social Welfare': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SOCWLF', 'Society and Genetics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SOCGEN', 'Sociology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SOCIOL', 'South Asian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SASIAN', 'Southeast Asian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SEASIAN', 'Spanish': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SPAN', 'Statistics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/STATS', 'Surgery': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SURGERY', 'Swahili': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SWAHILI', 'Thai': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/THAI', 'Theater': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/THEATER', 'Turkic Languages': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/TURKIC', 'Ukrainian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/UKRN', 'University Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/UNIVST', 'Urban Planning': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/URBNPL', 'Urology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/UROLOGY', 'Vietnamese': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/VIETMSE', 'World Arts and Cultures': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/WLARTS', 'Yiddish': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/YIDDSH'}
curr = []
missing = []

# print(composeSOCUrl(data))


# uploadAllClassesToDB()

# for key, value in data.items():
#     # if data[key][0] == "Anesthesiology":
#     #     continue
#     if data[key][0] not in catalogSubjects:
#         print(data[key][1] +" NOT IN THE DATA")
#         missing.append(data[key][1])
#         continue
#     try:
#         y = getClasses(catalogSubjects[data[key][0]], data[key][1])
#         curr.append(y)
#         print(curr)
#     except:
#         print("Error: " + data[key][1])

#     try:
#         with open('classdump4.json', 'w') as f:
#             json.dump(curr, f, indent = 4)
#     except:
#         print("Save fail: " + data[key][1])
# print(getClasses("https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOLCH" , "BIOL CH"))
# Anesthesiology, BIOL CH, community health sciences, MATH (last 2 pages)
# ['Graduate', 'Undergraduate', 'DESMA', 'ESL', 'LAW', 'Undergraduate', 'NEUROSC', 'Graduate']
# print(catalogSubjects)
# print(missing)
# getToSOCpage()
