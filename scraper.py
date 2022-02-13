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
import time
import selenium

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
    options = Options()
    options.headless = True
    s = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=options, service=s)
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
        links.append("https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName={longName}+{shortName}&t=22W&sBy=subject&subj={shortName}&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex".format(longName=longName, shortName=shortName))
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
    uniqueNames = {}
    thing = []
    for course in allCourses:
        print(course['Short name'])
        if course['Short name'] not in uniqueNames:
            uniqueNames[course['Short name']] = 0
            thing.append(course)
    print(uniqueNames)
    print(len(thing))
    # uniqueCourseList = {frozenset(item.items()) : item for item in allCourses}.values()
    # print(uniqueCourseList)
    collection.insert_one({"courses": thing})

def SOCMoreDetails(url):
    options = Options()
    options.headless = False
    s = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=options, service=s)
    driver.get(url)
    pages = ["bruh"]
    try:
        pages = (driver.execute_script(""" 
            let elems = document.querySelector("ucla-sa-soc-app").shadowRoot.querySelectorAll("#divPagination > div:nth-child(2) > ul > li");
            return elems;
        """))
    except:
        print("No pages")
    time.sleep(1)
    res = {}
    i = 0
    for k in range(2):
        j = 0
        if len(pages) == 0:
            pages = ["bruh"]
        for page in pages:
            try:
                # print(j)
                time.sleep(1)
                try:
                    driver.execute_script("""
                        document.querySelector('ucla-sa-soc-app').shadowRoot.querySelectorAll('#divPagination > div:nth-child(2) > ul > li')[arguments[0]].click();
                    """, j)
                except:
                    print("Single Page")
                time.sleep(2)

                j += 1
                driver.execute_script("""
                    let elems = document.querySelector("ucla-sa-soc-app").shadowRoot.querySelectorAll(".linkLikeButton");
                    elems.forEach((e) => e.click());
                """)
                time.sleep(3)

                # don't question it, it works. do not touch. bad. go away. danger
                links = (driver.execute_script("""
                    let links = [];
                    document.querySelector("ucla-sa-soc-app").shadowRoot.querySelectorAll("button.linkLikeButton").forEach((e) => {
                        links.push(e.getAttribute('data-poload'));
                    });
                    return links;

                """))
                time.sleep(3)
                for link in links:
                    if link == None:
                        continue
                    else:
                        classId = link[link.find('class_id') + 9:link.find('&class_no=')]
                        if classId in res:
                            continue
                        else:
                            res[classId] = "https://sa.ucla.edu/ro/Public/SOC/Results/ClassDetail?" + link.replace(' ', '%20')
                            i += 1
                # print(res)
                time.sleep(1)
            except:
                print("FAIL")
            
    # print(res)
    # print(i)
    driver.close()
    return res

def getDescription(link):
    s = Service(ChromeDriverManager().install())
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(service=s, options=options)
    driver.get(link)
    driver.implicitly_wait(3000)
    html = driver.execute_script('''return document.querySelector("ucla-sa-soc-app").shadowRoot;''')
    html = html.get("shadow-6066-11e4-a52e-4f735466cecf")
    subject = html.find_element(By.ID, "subject_class").get_attribute('innerHTML')
    description = html.find_element(By.ID, "section").text
    description = description[:description.find("Department")]
    start = subject.find('<br>')+5
    end = subject.find('-')-1
    name = ' '.join(subject[start:end].split())
    abbreviation = ""
    for i, val in enumerate(name):
        if(val.isdigit()):
            abbreviation = name[:i-1]
    fullName = subject[4:subject.find("(")-1]
    restrictions = html.find_elements(By.CLASS_NAME, "enrollment_info")[1].find_elements(By.TAG_NAME, "td")[1].text
    units = html.find_elements(By.CLASS_NAME, "enrl_mtng_info")[1].find_elements(By.TAG_NAME, "td")[5].text
    professor = html.find_elements(By.CLASS_NAME, "enrl_mtng_info")[1].find_elements(By.TAG_NAME, "td")[6].text
    requisites = html.find_elements(By.CLASS_NAME, "course_requisites")
    isOr = []
    currentQuarter = link[link.find("term_cd")+8:link.find("term_cd")+11]
    enforcedPrereqs = []
    optionalPrereqs = []
    enforcedCoreqs = []
    
    for i, val in enumerate(requisites[1:]):
        requisite = val.find_element(By.CLASS_NAME, "popover-right").text.strip(" and")
     
        if "or" in requisite:
            isOr.append(True)
        if(len(isOr) != 0 and isOr[i-i]==True and i==len(isOr)-1):
            isOr.append(True)
        else:
            isOr.append(False)
        requisite = requisite.strip(" or")
       # print(val.find_elements(By.TAG_NAME, "td")[1].text) minimum grade required
        isEnforcedCoreq = True if val.find_elements(By.TAG_NAME, "td")[3].text == "Yes" else False
        if(isEnforcedCoreq):
            enforcedCoreqs.append(requisite)
            break
        isEnforcedPrereq = True if val.find_elements(By.TAG_NAME, "td")[2].text == "Yes" and not isOr[i] else False
        if(isEnforcedPrereq) :
            enforcedPrereqs.append(requisite)
            break
        isOptionalPrereq = True if val.find_elements(By.TAG_NAME, "td")[2].text == "Yes" and isOr[i] else False
        if(isOptionalPrereq):
            optionalPrereqs.append(requisite)
            break

        #print(val.find_element(By.CLASS_NAME, "popover-link").get_attribute("data-content")) GETS EXTRA WARNING TEXT

    for preq in enforcedPrereqs:
        print(preq)

    Class = {"name": name, "subjectArea": fullName, "subjectAreaAbbreviation": abbreviation, "quartersOffered": currentQuarter, "units": units, "enforcedPrerequisites": enforcedPrereqs, "optionalPrerequisites": optionalPrereqs, "enforcedCorequisites": enforcedCoreqs, "description": description, "professor": professor, "restrictions": restrictions}
    
    print(Class)
    driver.close()
    client = MongoClient(os.environ.get("DB_URI"))
    db = client["onTrackDB"]
    collection = db["CoursesOffered"]

    # collection.insert_one(Class)

# Main

# subjects = getSubjectArea()
# for key, value in subjects.items():
#     subjects[key] = getSubjectName(value)

# print(subjects)
# catalogSubjects = getSubjectAreas()

data = {'Aerospace Studies': ['Aerospace Studies', 'AERO ST'], 'African American Studies': ['African American Studies', 'AF AMER'], 'African Studies': ['African Studies', 'AFRC ST'], 'American Indian Studies': ['American Indian Studies', 'AM IND'], 'American Sign Language': ['American Sign Language', 'ASL'], 'Ancient Near East': ['Ancient Near East', 'AN N EA'], 'Anesthesiology': ['Anesthesiology', 'ANES'], 'Anthropology': ['Anthropology', 'ANTHRO'], 'Applied Linguistics': ['Applied Linguistics', 'APPLING'], 'Arabic': ['Arabic', 'ARABIC'], 'Archaeology': ['Archaeology', 'ARCHEOL'], 'Architecture and Urban Design': ['Architecture and Urban Design', 'ARCH&UD'], 'Armenian': ['Armenian', 'ARMENIA'], 'Art': ['Art', 'ART'], 'Art History': ['Art History', 'ART HIS'], 'Arts and Architecture': ['Arts and Architecture', 'ART&ARC'], 'Arts Education': ['Arts Education', 'ARTS ED'], 'Asian': ['Asian', 'ASIAN'], 'Asian American Studies': ['Asian American Studies', 'ASIA AM'], 'Astronomy': ['Astronomy', 'ASTR'], 'Atmospheric and Oceanic Sciences': ['Atmospheric and Oceanic Sciences', 'A&O SCI'], 'Bioengineering': ['Bioengineering', 'BIOENGR'], 'Bioinformatics (Graduate)': ['Bioinformatics', 'Graduate', 'BIOINFO)'], 'Bioinformatics (Undergraduate)': ['Bioinformatics', 'Undergraduate', 'BIOINFR)'], 'Biological Chemistry': ['Biological Chemistry', 'BIOL CH'], 'Biomathematics': ['Biomathematics', 'BIOMATH'], 'Biomedical Research': ['Biomedical Research', 'BMD RES'], 'Biostatistics': ['Biostatistics', 'BIOSTAT'], 'Bulgarian': ['Bulgarian', 'BULGR'], 'Central and East European Studies': ['Central and East European Studies', 'C&EE ST'], 'Chemical Engineering': ['Chemical Engineering', 'CH ENGR'], 'Chemistry and Biochemistry': ['Chemistry and Biochemistry', 'CHEM'], 'Chicana/o and Central American Studies': ['Chicana/o and Central American Studies', 'CCAS'], 'Chinese': ['Chinese', 'CHIN'], 'Civil and Environmental Engineering': ['Civil and Environmental Engineering', 'C&EE'], 'Classics': ['Classics', 'CLASSIC'], 'Clusters': ['Clusters', 'CLUSTER'], 'Communication': ['Communication', 'COMM'], 'Community Engagement and Social Change': ['Community Engagement and Social Change', 'CESC'], 'Community Health Sciences': ['Community Health Sciences', 'COM HLT'], 'Comparative Literature': ['Comparative Literature', 'COM LIT'], 'Computational and Systems Biology': ['Computational and Systems Biology', 'C&S BIO'], 'Computer Science': ['Computer Science', 'COM SCI'], 'Conservation of Cultural Heritage': ['Conservation of Cultural Heritage', 'CLT HTG'], 'Czech': ['Czech', 'CZCH'], 'Dance': ['Dance', 'DANCE'], 'Dentistry': ['Dentistry', 'DENT'], 'Design / Media Arts': ['Design / Media Arts', 'DESMA'], 'Digital Humanities': ['Digital Humanities', 'DGT HUM'], 'Disability Studies': ['Disability Studies', 'DIS STD'], 'Dutch': ['Dutch', 'DUTCH'], 'Earth, Planetary, and Space Sciences': ['Earth, Planetary, and Space Sciences', 'EPS SCI'], 'East Asian Studies': ['East Asian Studies', 'EA STDS'], 'Ecology and Evolutionary Biology': ['Ecology and Evolutionary Biology', 'EE BIOL'], 'Economics': ['Economics', 'ECON'], 'Education': ['Education', 'EDUC'], 'Electrical and Computer Engineering': ['Electrical and Computer Engineering', 'EC ENGR'], 'Engineering': ['Engineering', 'ENGR'], 'English': ['English', 'ENGL'], 'English as A Second Language': ['English as A Second Language', 'ESL'], 'English Composition': ['English Composition', 'ENGCOMP'], 'Environment': ['Environment', 'ENVIRON'], 'Environmental Health Sciences': ['Environmental Health Sciences', 'ENV HLT'],'Epidemiology': ['Epidemiology', 'EPIDEM'], 'Ethnomusicology': ['Ethnomusicology', 'ETHNMUS'], 'European Languages and Transcultural Studies': ['European Languages and Transcultural Studies', 'ELTS'], 'Family Medicine': ['Family Medicine', 'FAM MED'], 'Filipino': ['Filipino', 'FILIPNO'], 'Film and Television': ['Film and Television', 'FILM TV'], 'Food Studies': ['Food Studies', 'FOOD ST'], 'French': ['French', 'FRNCH'], 'Gender Studies': ['Gender Studies', 'GENDER'], 'Geography': ['Geography', 'GEOG'], 'German': ['German', 'GERMAN'], 'Gerontology': ['Gerontology', 'GRNTLGY'], 'Global Health': ['Global Health', 'GLB HLT'], 'Global Jazz Studies': ['Global Jazz Studies', 'GJ STDS'], 'Global Studies': ['Global Studies', 'GLBL ST'], 'Graduate Student Professional Development': ['Graduate Student Professional Development', 'GRAD PD'], 'Greek': ['Greek', 'GREEK'], 'Health Policy and Management': ['Health Policy and Management', 'HLT POL'], 'Healthcare Administration': ['Healthcare Administration', 'HLT ADM'], 'Hebrew': ['Hebrew', 'HEBREW'], 'Hindi-Urdu': ['Hindi-Urdu', 'HIN-URD'], 'History': ['History', 'HIST'], 'Honors Collegium': ['Honors Collegium', 'HNRS'], 'Human Genetics': ['Human Genetics', 'HUM GEN'], 'Hungarian': ['Hungarian', 'HNGAR'], 'Indigenous Languages of the Americas': ['Indigenous Languages of the Americas', 'IL AMER'], 'Indo-European Studies': ['Indo-European Studies', 'I E STD'], 'Indonesian': ['Indonesian', 'INDO'], 'Information Studies': ['Information Studies', 'INF STD'], 'International and Area Studies': ['International and Area Studies', 'I A STD'], 'International Development Studies': ['International Development Studies', 'INTL DV'], 'International Migration Studies': ['International Migration Studies', 'I M STD'], 'Iranian': ['Iranian', 'IRANIAN'], 'Islamic Studies': ['Islamic Studies', 'ISLM ST'], 'Italian': ['Italian', 'ITALIAN'], 'Japanese': ['Japanese', 'JAPAN'], 'Jewish Studies': ['Jewish Studies', 'JEWISH'], 'Korean': ['Korean', 'KOREA'], 'Labor Studies': ['Labor Studies', 'LBR STD'], 'Latin': ['Latin', 'LATIN'], 'Latin American Studies': ['Latin American Studies', 'LATN AM'], 'Law': ['Law', 'LAW'], 'Law (Undergraduate)': ['Law', 'Undergraduate', 'UG-LAW)'], 'Lesbian, Gay, Bisexual, Transgender, and Queer Studies': ['Lesbian, Gay, Bisexual, Transgender, and Queer Studies', 'LGBTQS'], 'Life Sciences': ['Life Sciences', 'LIFESCI'], 'Linguistics': ['Linguistics', 'LING'], 'Lithuanian': ['Lithuanian', 'LTHUAN'], 'Management': ['Management', 'MGMT'], 'Management-Executive MBA': ['Management-Executive MBA', 'MGMTEX'], 'Management-Full-Time MBA': ['Management-Full-Time MBA', 'MGMTFT'], 'Management-Fully Employed MBA': ['Management-Fully Employed MBA', 'MGMTFE'], 'Management-Global Executive MBA Asia Pacific': ['Management-Global Executive MBA Asia Pacific', 'MGMTGEX'], 'Management-Master of Financial Engineering': ['Management-Master of Financial Engineering', 'MGMTMFE'], 'Management-Master of Science in Business Analytics': ['Management-Master of Science in Business Analytics', 'MGMTMSA'], 'Management-PhD': ['Management-PhD', 'MGMTPHD'], 'Materials Science and Engineering': ['Materials Science and Engineering', 'MAT SCI'], 'Mathematics': ['Mathematics', 'MATH'], 'Mechanical and Aerospace Engineering': ['Mechanical and Aerospace Engineering', 'MECH&AE'], 'Medical History': ['Medical History', 'MED HIS'], 'Medicine': ['Medicine', 'MED'], 'Microbiology, Immunology, and Molecular Genetics': ['Microbiology, Immunology, and Molecular Genetics', 'MIMG'], 'Middle Eastern Studies': ['Middle Eastern Studies', 'M E STD'], 'Military Science': ['Military Science', 'MIL SCI'], 'Molecular and Medical Pharmacology': ['Molecular and Medical Pharmacology', 'M PHARM'], 'Molecular Biology': ['Molecular Biology', 'MOL BIO'], 'Molecular Toxicology': ['Molecular Toxicology', 'MOL TOX'], 'Molecular, Cell, and Developmental Biology': ['Molecular, Cell, and Developmental Biology', 'MCD BIO'], 'Molecular, Cellular, and Integrative Physiology': ['Molecular, Cellular, and Integrative Physiology', 'MC&IP'], 'Music': ['Music', 'MUSC'], 'Music Industry': ['Music Industry', 'MSC IND'], 'Musicology': ['Musicology', 'MUSCLG'], 'Naval Science': ['Naval Science', 'NAV SCI'], 'Near Eastern Languages': ['Near Eastern Languages', 'NR EAST'], 'Neurobiology': ['Neurobiology', 'NEURBIO'], 'Neurology': ['Neurology', 'NEURLGY'], 'Neuroscience': ['Neuroscience', 'NEUROSC'], 'Neuroscience (Graduate)': ['Neuroscience', 'Graduate', 'NEURO)'], 'Neurosurgery': ['Neurosurgery', 'NEURSGY'], 'Nursing': ['Nursing', 'NURSING'], 'Obstetrics and Gynecology': ['Obstetrics and Gynecology', 'OBGYN'], 'Ophthalmology': ['Ophthalmology', 'OPTH'], 'Oral Biology': ['Oral Biology', 'ORL BIO'], 'Orthopaedic Surgery': ['Orthopaedic Surgery', 'ORTHPDC'], 'Pathology and Laboratory Medicine': ['Pathology and Laboratory Medicine', 'PATH'], 'Pediatrics': ['Pediatrics', 'PEDS'], 'Philosophy': ['Philosophy', 'PHILOS'], 'Physics': ['Physics', 'PHYSICS'], 'Physics and Biology in Medicine': ['Physics and Biology in Medicine', 'PBMED'], 'Physiological Science': ['Physiological Science', 'PHYSCI'], 'Physiology': ['Physiology', 'PHYSIOL'], 'Polish': ['Polish', 'POLSH'], 'Political Science': ['Political Science', 'POL SCI'], 'Portuguese': ['Portuguese', 'PORTGSE'], 'Program in Computing': ['Program in Computing', 'COMPTNG'], 'Psychiatry and Biobehavioral Sciences': ['Psychiatry and Biobehavioral Sciences', 'PSYCTRY'], 'Psychology': ['Psychology', 'PSYCH'], 'Public Affairs': ['Public Affairs', 'PUB AFF'], 'Public Health': ['Public Health', 'PUB HLT'], 'Public Policy': ['Public Policy', 'PUB PLC'], 'Radiation Oncology': ['Radiation Oncology', 'RAD ONC'], 'Religion, Study of': ['Religion, Study of', 'RELIGN'], 'Romanian': ['Romanian', 'ROMANIA'], 'Russian': ['Russian', 'RUSSN'], 'Scandinavian': ['Scandinavian', 'SCAND'], 'Science Education': ['Science Education', 'SCI EDU'], 'Semitic': ['Semitic', 'SEMITIC'], 'Serbian/Croatian': ['Serbian/Croatian', 'SRB CRO'], 'Slavic': ['Slavic', 'SLAVC'], 'Social Science': ['Social Science', 'SOC SC'], 'Social Thought': ['Social Thought', 'SOC THT'], 'Social Welfare': ['Social Welfare', 'SOC WLF'], 'Society and Genetics': ['Society and Genetics', 'SOC GEN'], 'Sociology': ['Sociology', 'SOCIOL'], 'South Asian': ['South Asian', 'S ASIAN'], 'Southeast Asian': ['Southeast Asian', 'SEASIAN'], 'Spanish': ['Spanish', 'SPAN'], 'Statistics': ['Statistics', 'STATS'], 'Surgery': ['Surgery', 'SURGERY'], 'Swahili': ['Swahili', 'SWAHILI'], 'Thai': ['Thai', 'THAI'], 'Theater': ['Theater', 'THEATER'], 'Turkic Languages': ['Turkic Languages', 'TURKIC'], 'Ukrainian': ['Ukrainian', 'UKRN'], 'University Studies': ['University Studies', 'UNIV ST'], 'Urban Planning': ['Urban Planning', 'URBN PL'], 'Urology': ['Urology', 'UROLOGY'], 'Vietnamese': ['Vietnamese', 'VIETMSE'], 'World Arts and Cultures': ['World Arts and Cultures', 'WL ARTS'], 'Yiddish': ['Yiddish', 'YIDDSH']}

# catalogSubjects = {'Aerospace Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/AEROST', 'African American Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/AFAMER', 'African Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/AFRCST', 'American Indian Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/AMIND', 'American Sign Language': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ASL', 'Ancient Near East': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ANNEA', 'Anesthesiology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ANES', 'Anthropology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ANTHRO', 'Applied Linguistics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/APPLING', 'Arabic': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARABIC', 'Archaeology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARCHEOL', 'Architecture and Urban Design': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARCHUD', 'Armenian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARMENIA', 'Art': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ART', 'Art History': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARTHIS', 'Arts Education': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARTSED', 'Arts and Architecture': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARTARC', 'Asian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ASIAN', 'Asian American Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ASIAAM', 'Astronomy': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ASTR', 'Atmospheric and Oceanic Sciences': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/AOSCI', 'Bioengineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOENGR', 

# catalogSubjects = {'Bioinformatics, Graduate': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOINFO', 'Bioinformatics, Undergraduate': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOINFR', 'Biological Chemistry': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOLCH', 'Biomathematics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOMATH', 'Biomedical Research': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BMDRES', 'Biostatistics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BIOSTAT', 'Bulgarian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/BULGR', 'Central and East European Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CEEST', 'Chemical Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CHENGR', 'Chemistry and Biochemistry': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CHEM', 'Chicana/o and Central American Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CCAS', 'Chinese': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CHIN', 'Civil and Environmental Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CEE', 'Classics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CLASSIC', 'Clusters': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CLUSTER', 'Communication': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/COMM', 'Community Engagement and Social Change': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CESC', 'Community Health Sciences': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/COMHLT', 'Comparative Literature': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/COMLIT', 'Computational and Systems Biology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CSBIO', 'Computer Science': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/COMSCI', 'Conservation of Cultural Heritage': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CLTHTG', 'Czech': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/CZCH', 'Dance': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/DANCE', 'Dentistry': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/DENT', 'Design|Media Arts': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/DESMA', 'Digital Humanities': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/DGTHUM', 'Disability Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/DISSTD', 'Dutch': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/DUTCH', 'Earth, Planetary, and Space Sciences': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/EPSSCI', 'East Asian Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/EASTDS', 'Ecology and Evolutionary Biology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/EEBIOL', 'Economics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ECON', 'Education': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/EDUC', 'Electrical and Computer Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ECENGR', 'Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ENGR', 'English': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ENGL', 'English Composition': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ENGCOMP', 'English as a Second Language': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ESL', 'Environment': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ENVIRON', 'Environmental Health Sciences': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ENVHLT', 'Epidemiology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/EPIDEM', 'Ethnomusicology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ETHNMUS', 'European Languages and Transcultural Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ELTS', 'Family Medicine': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/FAMMED', 'Filipino': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/FILIPNO', 'Film and Television': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/FILMTV', 'Food Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/FOODST', 'French': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/FRNCH', 'Gender Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GENDER', 'Geography': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GEOG', 'German': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GERMAN', 'Gerontology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GRNTLGY', 'Global Health': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GLBHLT', 'Global Jazz Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GJSTDS', 'Global Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GLBLST', 'Graduate Student Professional Development': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GRADPD', 'Greek': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/GREEK', 'Health Policy and Management': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HLTPOL', 'Healthcare Administration': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HLTADM', 'Hebrew': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HEBREW',

# catalogSubjects = {'Hindi-Urdu': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HINURD', 'History': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HIST', 'Honors Collegium': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HNRS', 'Human Genetics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HUMGEN', 'Hungarian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/HNGAR', 'Indigenous Languages of the Americas': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ILAMER', 'Indo-European Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/IESTD', 'Indonesian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/INDO', 'Information Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/INFSTD', 'International Development Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/INTLDV', 'International Migration Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/IMSTD', 'International and Area Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/IASTD', 'Iranian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/IRANIAN', 'Islamic Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ISLMST', 'Italian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ITALIAN', 'Japanese': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/JAPAN', 'Jewish Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/JEWISH', 'Korean': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/KOREA', 'Labor Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LBRSTD', 'Latin': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LATIN', 'Latin American Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LATNAM', 

# catalogSubjects = {'Law, Undergraduate': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/UGLAW', 'Lesbian, Gay, Bisexual, Transgender, and Queer Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LGBTQS', 'Life Sciences': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LIFESCI', 'Linguistics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LING', 'Lithuanian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/LTHUAN', 'Management': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMT', 'Management-Executive MBA': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTEX', 'Management-Full-Time MBA': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTFT', 'Management-Fully Employed MBA': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTFE', 'Management-Global Executive MBA Asia Pacific': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTGEX', 'Management-Master of Financial Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTMFE', 'Management-Master of Science in Business Analytics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTMSA', 'Management-PhD': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MGMTPHD', 'Materials Science and Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MATSCI', 'Mathematics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MATH', 'Mechanical and Aerospace Engineering': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MECHAE', 'Medical History': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MEDHIS', 'Medicine': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MED', 'Microbiology, Immunology, and Molecular Genetics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MIMG', 'Middle Eastern Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MESTD', 'Military Science': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MILSCI', 'Molecular Biology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MOLBIO', 'Molecular Toxicology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MOLTOX', 'Molecular and Medical Pharmacology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MPHARM', 'Molecular, Cell, and Developmental Biology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MCDBIO', 'Molecular, Cellular, and Integrative Physiology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MCIP', 'Music': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MUSC', 'Music Industry': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MSCIND', 'Musicology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/MUSCLG', 'Naval Science': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NAVSCI', 'Near Eastern Languages': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NREAST', 'Neurobiology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NEURBIO', 'Neurology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NEURLGY', 

catalogSubjects = {'Neuroscience, Graduate': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NEURO', 'Neuroscience, Undergraduate': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NEUROSC', 'Neurosurgery': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NEURSGY', 'Nursing': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/NURSING', 'Obstetrics and Gynecology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/OBGYN', 'Ophthalmology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/OPTH', 'Oral Biology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ORLBIO', 'Orthopaedic Surgery': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ORTHPDC', 'Pathology and Laboratory Medicine': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PATH', 'Pediatrics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PEDS', 'Philosophy': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PHILOS', 'Physics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PHYSICS', 'Physics and Biology in Medicine': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PBMED', 'Physiological Science': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PHYSCI', 'Physiology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PHYSIOL', 'Polish': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/POLSH', 'Political Science': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/POLSCI', 'Portuguese': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PORTGSE', 'Program in Computing': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/COMPTNG', 'Psychiatry and Biobehavioral Sciences': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PSYCTRY', 'Psychology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PSYCH', 'Public Affairs': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PUBAFF', 'Public Health': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PUBHLT', 'Public Policy': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/PUBPLC', 'Radiation Oncology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/RADONC', 'Religion, Study of': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/RELIGN', 'Romanian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ROMANIA', 'Russian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/RUSSN', 'Scandinavian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SCAND', 'Science Education': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SCIEDU', 'Semitic': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SEMITIC', 'Serbian/Croatian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SRBCRO', 'Slavic': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SLAVC', 'Social Science': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SOCSC', 'Social Thought': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SOCTHT', 'Social Welfare': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SOCWLF', 'Society and Genetics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SOCGEN', 'Sociology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SOCIOL', 'South Asian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SASIAN', 'Southeast Asian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SEASIAN', 'Spanish': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SPAN', 'Statistics': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/STATS', 'Surgery': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SURGERY', 'Swahili': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/SWAHILI', 'Thai': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/THAI', 'Theater': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/THEATER', 'Turkic Languages': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/TURKIC', 'Ukrainian': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/UKRN', 'University Studies': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/UNIVST', 'Urban Planning': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/URBNPL', 'Urology': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/UROLOGY', 'Vietnamese': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/VIETMSE', 'World Arts and Cultures': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/WLARTS', 'Yiddish': 'https://catalog.registrar.ucla.edu/browse/Subject%20Areas/YIDDSH'}
curr = []
missing = []


# print(composeSOCUrl(data))
# uploadAllClassesToDB()

# SOCUrl = composeSOCUrl(data)
SOCUrl = ['https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Aerospace+Studies+AERO+ST&t=22W&sBy=subject&subj=AERO+ST&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=African+American+Studies+AF+AMER&t=22W&sBy=subject&subj=AF+AMER&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=African+Studies+AFRC+ST&t=22W&sBy=subject&subj=AFRC+ST&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=American+Indian+Studies+AM+IND&t=22W&sBy=subject&subj=AM+IND&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=American+Sign+Language+ASL&t=22W&sBy=subject&subj=ASL&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Ancient+Near+East+AN+N+EA&t=22W&sBy=subject&subj=AN+N+EA&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Anesthesiology+ANES&t=22W&sBy=subject&subj=ANES&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Anthropology+ANTHRO&t=22W&sBy=subject&subj=ANTHRO&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Applied+Linguistics+APPLING&t=22W&sBy=subject&subj=APPLING&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Arabic+ARABIC&t=22W&sBy=subject&subj=ARABIC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Archaeology+ARCHEOL&t=22W&sBy=subject&subj=ARCHEOL&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Architecture+and+Urban+Design+ARCH&UD&t=22W&sBy=subject&subj=ARCH&UD&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Armenian+ARMENIA&t=22W&sBy=subject&subj=ARMENIA&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Art+ART&t=22W&sBy=subject&subj=ART&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Art+History+ART+HIS&t=22W&sBy=subject&subj=ART+HIS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Arts+and+Architecture+ART&ARC&t=22W&sBy=subject&subj=ART&ARC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Arts+Education+ARTS+ED&t=22W&sBy=subject&subj=ARTS+ED&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Asian+ASIAN&t=22W&sBy=subject&subj=ASIAN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Asian+American+Studies+ASIA+AM&t=22W&sBy=subject&subj=ASIA+AM&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Astronomy+ASTR&t=22W&sBy=subject&subj=ASTR&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Atmospheric+and+Oceanic+Sciences+A&O+SCI&t=22W&sBy=subject&subj=A&O+SCI&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Bioengineering+BIOENGR&t=22W&sBy=subject&subj=BIOENGR&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Bioinformatics+(Graduate)+Graduate&t=22W&sBy=subject&subj=Graduate&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Bioinformatics+(Undergraduate)+Undergraduate&t=22W&sBy=subject&subj=Undergraduate&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Biological+Chemistry+BIOL+CH&t=22W&sBy=subject&subj=BIOL+CH&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Biomathematics+BIOMATH&t=22W&sBy=subject&subj=BIOMATH&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Biomedical+Research+BMD+RES&t=22W&sBy=subject&subj=BMD+RES&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Biostatistics+BIOSTAT&t=22W&sBy=subject&subj=BIOSTAT&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Bulgarian+BULGR&t=22W&sBy=subject&subj=BULGR&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Central+and+East+European+Studies+C&EE+ST&t=22W&sBy=subject&subj=C&EE+ST&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Chemical+Engineering+CH+ENGR&t=22W&sBy=subject&subj=CH+ENGR&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Chemistry+and+Biochemistry+CHEM&t=22W&sBy=subject&subj=CHEM&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Chicana/o+and+Central+American+Studies+CCAS&t=22W&sBy=subject&subj=CCAS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Chinese+CHIN&t=22W&sBy=subject&subj=CHIN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Civil+and+Environmental+Engineering+C&EE&t=22W&sBy=subject&subj=C&EE&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Classics+CLASSIC&t=22W&sBy=subject&subj=CLASSIC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Clusters+CLUSTER&t=22W&sBy=subject&subj=CLUSTER&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Communication+COMM&t=22W&sBy=subject&subj=COMM&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Community+Engagement+and+Social+Change+CESC&t=22W&sBy=subject&subj=CESC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Community+Health+Sciences+COM+HLT&t=22W&sBy=subject&subj=COM+HLT&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Comparative+Literature+COM+LIT&t=22W&sBy=subject&subj=COM+LIT&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Computational+and+Systems+Biology+C&S+BIO&t=22W&sBy=subject&subj=C&S+BIO&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Computer+Science+COM+SCI&t=22W&sBy=subject&subj=COM+SCI&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Conservation+of+Cultural+Heritage+CLT+HTG&t=22W&sBy=subject&subj=CLT+HTG&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Czech+CZCH&t=22W&sBy=subject&subj=CZCH&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Dance+DANCE&t=22W&sBy=subject&subj=DANCE&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Dentistry+DENT&t=22W&sBy=subject&subj=DENT&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Design+/+Media+Arts+DESMA&t=22W&sBy=subject&subj=DESMA&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Digital+Humanities+DGT+HUM&t=22W&sBy=subject&subj=DGT+HUM&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Disability+Studies+DIS+STD&t=22W&sBy=subject&subj=DIS+STD&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Dutch+DUTCH&t=22W&sBy=subject&subj=DUTCH&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Earth,+Planetary,+and+Space+Sciences+EPS+SCI&t=22W&sBy=subject&subj=EPS+SCI&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=East+Asian+Studies+EA+STDS&t=22W&sBy=subject&subj=EA+STDS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Ecology+and+Evolutionary+Biology+EE+BIOL&t=22W&sBy=subject&subj=EE+BIOL&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Economics+ECON&t=22W&sBy=subject&subj=ECON&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Education+EDUC&t=22W&sBy=subject&subj=EDUC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Electrical+and+Computer+Engineering+EC+ENGR&t=22W&sBy=subject&subj=EC+ENGR&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Engineering+ENGR&t=22W&sBy=subject&subj=ENGR&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=English+ENGL&t=22W&sBy=subject&subj=ENGL&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=English+as+A+Second+Language+ESL&t=22W&sBy=subject&subj=ESL&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=English+Composition+ENGCOMP&t=22W&sBy=subject&subj=ENGCOMP&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Environment+ENVIRON&t=22W&sBy=subject&subj=ENVIRON&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Environmental+Health+Sciences+ENV+HLT&t=22W&sBy=subject&subj=ENV+HLT&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Epidemiology+EPIDEM&t=22W&sBy=subject&subj=EPIDEM&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Ethnomusicology+ETHNMUS&t=22W&sBy=subject&subj=ETHNMUS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=European+Languages+and+Transcultural+Studies+ELTS&t=22W&sBy=subject&subj=ELTS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Family+Medicine+FAM+MED&t=22W&sBy=subject&subj=FAM+MED&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Filipino+FILIPNO&t=22W&sBy=subject&subj=FILIPNO&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Film+and+Television+FILM+TV&t=22W&sBy=subject&subj=FILM+TV&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Food+Studies+FOOD+ST&t=22W&sBy=subject&subj=FOOD+ST&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=French+FRNCH&t=22W&sBy=subject&subj=FRNCH&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Gender+Studies+GENDER&t=22W&sBy=subject&subj=GENDER&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Geography+GEOG&t=22W&sBy=subject&subj=GEOG&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=German+GERMAN&t=22W&sBy=subject&subj=GERMAN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Gerontology+GRNTLGY&t=22W&sBy=subject&subj=GRNTLGY&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Global+Health+GLB+HLT&t=22W&sBy=subject&subj=GLB+HLT&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Global+Jazz+Studies+GJ+STDS&t=22W&sBy=subject&subj=GJ+STDS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Global+Studies+GLBL+ST&t=22W&sBy=subject&subj=GLBL+ST&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Graduate+Student+Professional+Development+GRAD+PD&t=22W&sBy=subject&subj=GRAD+PD&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Greek+GREEK&t=22W&sBy=subject&subj=GREEK&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Health+Policy+and+Management+HLT+POL&t=22W&sBy=subject&subj=HLT+POL&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Healthcare+Administration+HLT+ADM&t=22W&sBy=subject&subj=HLT+ADM&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Hebrew+HEBREW&t=22W&sBy=subject&subj=HEBREW&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Hindi-Urdu+HIN-URD&t=22W&sBy=subject&subj=HIN-URD&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=History+HIST&t=22W&sBy=subject&subj=HIST&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Honors+Collegium+HNRS&t=22W&sBy=subject&subj=HNRS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Human+Genetics+HUM+GEN&t=22W&sBy=subject&subj=HUM+GEN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Hungarian+HNGAR&t=22W&sBy=subject&subj=HNGAR&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Indigenous+Languages+of+the+Americas+IL+AMER&t=22W&sBy=subject&subj=IL+AMER&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Indo-European+Studies+I+E+STD&t=22W&sBy=subject&subj=I+E+STD&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Indonesian+INDO&t=22W&sBy=subject&subj=INDO&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Information+Studies+INF+STD&t=22W&sBy=subject&subj=INF+STD&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=International+and+Area+Studies+I+A+STD&t=22W&sBy=subject&subj=I+A+STD&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=International+Development+Studies+INTL+DV&t=22W&sBy=subject&subj=INTL+DV&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=International+Migration+Studies+I+M+STD&t=22W&sBy=subject&subj=I+M+STD&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Iranian+IRANIAN&t=22W&sBy=subject&subj=IRANIAN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Islamic+Studies+ISLM+ST&t=22W&sBy=subject&subj=ISLM+ST&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Italian+ITALIAN&t=22W&sBy=subject&subj=ITALIAN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Japanese+JAPAN&t=22W&sBy=subject&subj=JAPAN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Jewish+Studies+JEWISH&t=22W&sBy=subject&subj=JEWISH&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Korean+KOREA&t=22W&sBy=subject&subj=KOREA&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Labor+Studies+LBR+STD&t=22W&sBy=subject&subj=LBR+STD&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Latin+LATIN&t=22W&sBy=subject&subj=LATIN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Latin+American+Studies+LATN+AM&t=22W&sBy=subject&subj=LATN+AM&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Law+LAW&t=22W&sBy=subject&subj=LAW&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Law+(Undergraduate)+Undergraduate&t=22W&sBy=subject&subj=Undergraduate&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Lesbian,+Gay,+Bisexual,+Transgender,+and+Queer+Studies+LGBTQS&t=22W&sBy=subject&subj=LGBTQS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Life+Sciences+LIFESCI&t=22W&sBy=subject&subj=LIFESCI&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Linguistics+LING&t=22W&sBy=subject&subj=LING&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Lithuanian+LTHUAN&t=22W&sBy=subject&subj=LTHUAN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Management+MGMT&t=22W&sBy=subject&subj=MGMT&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Management-Executive+MBA+MGMTEX&t=22W&sBy=subject&subj=MGMTEX&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Management-Full-Time+MBA+MGMTFT&t=22W&sBy=subject&subj=MGMTFT&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Management-Fully+Employed+MBA+MGMTFE&t=22W&sBy=subject&subj=MGMTFE&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Management-Global+Executive+MBA+Asia+Pacific+MGMTGEX&t=22W&sBy=subject&subj=MGMTGEX&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Management-Master+of+Financial+Engineering+MGMTMFE&t=22W&sBy=subject&subj=MGMTMFE&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Management-Master+of+Science+in+Business+Analytics+MGMTMSA&t=22W&sBy=subject&subj=MGMTMSA&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Management-PhD+MGMTPHD&t=22W&sBy=subject&subj=MGMTPHD&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Materials+Science+and+Engineering+MAT+SCI&t=22W&sBy=subject&subj=MAT+SCI&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Mathematics+MATH&t=22W&sBy=subject&subj=MATH&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Mechanical+and+Aerospace+Engineering+MECH&AE&t=22W&sBy=subject&subj=MECH&AE&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Medical+History+MED+HIS&t=22W&sBy=subject&subj=MED+HIS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Medicine+MED&t=22W&sBy=subject&subj=MED&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Microbiology,+Immunology,+and+Molecular+Genetics+MIMG&t=22W&sBy=subject&subj=MIMG&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Middle+Eastern+Studies+M+E+STD&t=22W&sBy=subject&subj=M+E+STD&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Military+Science+MIL+SCI&t=22W&sBy=subject&subj=MIL+SCI&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Molecular+and+Medical+Pharmacology+M+PHARM&t=22W&sBy=subject&subj=M+PHARM&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Molecular+Biology+MOL+BIO&t=22W&sBy=subject&subj=MOL+BIO&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Molecular+Toxicology+MOL+TOX&t=22W&sBy=subject&subj=MOL+TOX&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Molecular,+Cell,+and+Developmental+Biology+MCD+BIO&t=22W&sBy=subject&subj=MCD+BIO&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Molecular,+Cellular,+and+Integrative+Physiology+MC&IP&t=22W&sBy=subject&subj=MC&IP&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Music+MUSC&t=22W&sBy=subject&subj=MUSC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Music+Industry+MSC+IND&t=22W&sBy=subject&subj=MSC+IND&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Musicology+MUSCLG&t=22W&sBy=subject&subj=MUSCLG&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Naval+Science+NAV+SCI&t=22W&sBy=subject&subj=NAV+SCI&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Near+Eastern+Languages+NR+EAST&t=22W&sBy=subject&subj=NR+EAST&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Neurobiology+NEURBIO&t=22W&sBy=subject&subj=NEURBIO&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Neurology+NEURLGY&t=22W&sBy=subject&subj=NEURLGY&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Neuroscience+NEUROSC&t=22W&sBy=subject&subj=NEUROSC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Neuroscience+(Graduate)+Graduate&t=22W&sBy=subject&subj=Graduate&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Neurosurgery+NEURSGY&t=22W&sBy=subject&subj=NEURSGY&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Nursing+NURSING&t=22W&sBy=subject&subj=NURSING&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Obstetrics+and+Gynecology+OBGYN&t=22W&sBy=subject&subj=OBGYN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Ophthalmology+OPTH&t=22W&sBy=subject&subj=OPTH&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Oral+Biology+ORL+BIO&t=22W&sBy=subject&subj=ORL+BIO&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Orthopaedic+Surgery+ORTHPDC&t=22W&sBy=subject&subj=ORTHPDC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Pathology+and+Laboratory+Medicine+PATH&t=22W&sBy=subject&subj=PATH&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Pediatrics+PEDS&t=22W&sBy=subject&subj=PEDS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Philosophy+PHILOS&t=22W&sBy=subject&subj=PHILOS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Physics+PHYSICS&t=22W&sBy=subject&subj=PHYSICS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Physics+and+Biology+in+Medicine+PBMED&t=22W&sBy=subject&subj=PBMED&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Physiological+Science+PHYSCI&t=22W&sBy=subject&subj=PHYSCI&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Physiology+PHYSIOL&t=22W&sBy=subject&subj=PHYSIOL&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Polish+POLSH&t=22W&sBy=subject&subj=POLSH&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Political+Science+POL+SCI&t=22W&sBy=subject&subj=POL+SCI&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Portuguese+PORTGSE&t=22W&sBy=subject&subj=PORTGSE&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Program+in+Computing+COMPTNG&t=22W&sBy=subject&subj=COMPTNG&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Psychiatry+and+Biobehavioral+Sciences+PSYCTRY&t=22W&sBy=subject&subj=PSYCTRY&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Psychology+PSYCH&t=22W&sBy=subject&subj=PSYCH&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Public+Affairs+PUB+AFF&t=22W&sBy=subject&subj=PUB+AFF&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Public+Health+PUB+HLT&t=22W&sBy=subject&subj=PUB+HLT&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Public+Policy+PUB+PLC&t=22W&sBy=subject&subj=PUB+PLC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Radiation+Oncology+RAD+ONC&t=22W&sBy=subject&subj=RAD+ONC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Religion,+Study+of+RELIGN&t=22W&sBy=subject&subj=RELIGN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Romanian+ROMANIA&t=22W&sBy=subject&subj=ROMANIA&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Russian+RUSSN&t=22W&sBy=subject&subj=RUSSN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Scandinavian+SCAND&t=22W&sBy=subject&subj=SCAND&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Science+Education+SCI+EDU&t=22W&sBy=subject&subj=SCI+EDU&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Semitic+SEMITIC&t=22W&sBy=subject&subj=SEMITIC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Serbian/Croatian+SRB+CRO&t=22W&sBy=subject&subj=SRB+CRO&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Slavic+SLAVC&t=22W&sBy=subject&subj=SLAVC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Social+Science+SOC+SC&t=22W&sBy=subject&subj=SOC+SC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Social+Thought+SOC+THT&t=22W&sBy=subject&subj=SOC+THT&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Social+Welfare+SOC+WLF&t=22W&sBy=subject&subj=SOC+WLF&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Society+and+Genetics+SOC+GEN&t=22W&sBy=subject&subj=SOC+GEN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Sociology+SOCIOL&t=22W&sBy=subject&subj=SOCIOL&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=South+Asian+S+ASIAN&t=22W&sBy=subject&subj=S+ASIAN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Southeast+Asian+SEASIAN&t=22W&sBy=subject&subj=SEASIAN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Spanish+SPAN&t=22W&sBy=subject&subj=SPAN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Statistics+STATS&t=22W&sBy=subject&subj=STATS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Surgery+SURGERY&t=22W&sBy=subject&subj=SURGERY&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Swahili+SWAHILI&t=22W&sBy=subject&subj=SWAHILI&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Thai+THAI&t=22W&sBy=subject&subj=THAI&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Theater+THEATER&t=22W&sBy=subject&subj=THEATER&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Turkic+Languages+TURKIC&t=22W&sBy=subject&subj=TURKIC&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Ukrainian+UKRN&t=22W&sBy=subject&subj=UKRN&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=University+Studies+UNIV+ST&t=22W&sBy=subject&subj=UNIV+ST&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Urban+Planning+URBN+PL&t=22W&sBy=subject&subj=URBN+PL&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Urology+UROLOGY&t=22W&sBy=subject&subj=UROLOGY&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Vietnamese+VIETMSE&t=22W&sBy=subject&subj=VIETMSE&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=World+Arts+and+Cultures+WL+ARTS&t=22W&sBy=subject&subj=WL+ARTS&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex', 'https://sa.ucla.edu/ro/public/soc/Results?SubjectAreaName=Yiddish+YIDDSH&t=22W&sBy=subject&subj=YIDDSH&catlg=&cls_no=&undefined=Go&btnIsInIndex=btn_inIndex']


def updatedSOCGrabbing(url):
    print(url)
    res = []
    options = Options()
    options.headless = True
    s = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=options, service=s)
    driver.get(url)
    badShortName = url.split('/')[-1]
    time.sleep(1)
    while True:
        links = driver.execute_script("""
            let elems = document.querySelectorAll('a.cs-list-item.css-1hhgbew-Links--StyledLink-Links--StyledAILink.e1t6s54p8')

        return elems;
        """)

        if len(links) == 0:
            break

        time.sleep(1)
        for link in links:
                temp = {}
                shortName = badNameToGood[badShortName] + " " + link.get_attribute('href').split('/')[-1][len(badShortName):]
                temp["Short name"] = shortName
                temp["Full name"] = link.find_element_by_css_selector('div > div.unit-title').text
                res.append(temp)
        time.sleep(2)
        x = driver.execute_script("""
            return document.getElementById('pagination-page-next').disabled
        """)

        if x:
            break

        driver.execute_script("document.getElementById('pagination-page-next').click()")
        time.sleep(1)
    driver.close()
    return res

# getDescription("https://sa.ucla.edu/ro/Public/SOC/Results/ClassDetail?term_cd=22W&subj_area_cd=BIOENGR&crs_catlg_no=0596%20%20%20%20&class_id=650960272&class_no=%20072%20%20")

badNameToGood = {'AEROST': 'AERO ST', 'AFAMER': 'AF AMER', 'AFRCST': 'AFRC ST', 'AMIND': 'AM IND', 'ASL': 'ASL', 'ANNEA': 'AN N EA', 'ANES': 'ANES', 'ANTHRO': 'ANTHRO', 'APPLING': 'APPLING', 'ARABIC': 'ARABIC', 'ARCHEOL': 'ARCHEOL', 'ARCHUD': 'ARCH&UD', 'ARMENIA': 'ARMENIA', 'ART': 'ART', 'ARTHIS': 'ART HIS', 'ARTARC': 'ART&ARC', 'ARTSED': 'ARTS ED', 'ASIAN': 'ASIAN', 'ASIAAM': 'ASIA AM', 'ASTR': 'ASTR', 'AOSCI': 'A&O SCI', 'BIOENGR': 'BIOENGR', 'BIOINFO': 'BIOINFO', 'BIOINFR': 'BIOINFR', 'BIOLCH': 'BIOL CH', 'BIOMATH': 'BIOMATH', 'BMDRES': 'BMD RES', 'BIOSTAT': 'BIOSTAT', 'BULGR': 'BULGR', 'CEEST': 'C&EE ST', 'CHENGR': 'CH ENGR', 'CHEM': 'CHEM', 'CCAS': 'CCAS', 'CHIN': 'CHIN', 'CEE': 'C&EE', 'CLASSIC': 'CLASSIC', 'CLUSTER': 'CLUSTER', 'COMM': 'COMM', 'CESC': 'CESC', 'COMHLT': 'COM HLT', 'COMLIT': 'COM LIT', 'CSBIO': 'C&S BIO', 'COMSCI': 'COM SCI', 'CLTHTG': 'CLT HTG', 'CZCH': 'CZCH', 'DANCE': 'DANCE', 'DENT': 'DENT', 'DESMA': 'DESMA', 'DGTHUM': 'DGT HUM', 'DISSTD': 'DIS STD', 'DUTCH': 'DUTCH', 'EPSSCI': 'EPS SCI', 'EASTDS': 'EA STDS', 'EEBIOL': 'EE BIOL', 'ECON': 'ECON', 'EDUC': 'EDUC', 'ECENGR': 'EC ENGR', 'ENGR': 'ENGR', 'ENGL': 'ENGL', 'ESL': 'ESL', 'ENGCOMP': 'ENGCOMP', 'ENVIRON': 'ENVIRON', 'ENVHLT': 'ENV HLT', 'EPIDEM': 'EPIDEM', 'ETHNMUS': 'ETHNMUS', 'ELTS': 'ELTS', 'FAMMED': 'FAM MED', 'FILIPNO': 'FILIPNO', 'FILMTV': 'FILM TV', 'FOODST': 'FOOD ST', 'FRNCH': 'FRNCH', 'GENDER': 'GENDER', 'GEOG': 'GEOG', 'GERMAN': 'GERMAN', 'GRNTLGY': 'GRNTLGY', 'GLBHLT': 'GLB HLT', 'GJSTDS': 'GJ STDS', 'GLBLST': 'GLBL ST', 'GRADPD': 'GRAD PD', 'GREEK': 'GREEK', 'HLTPOL': 'HLT POL', 'HLTADM': 'HLT ADM', 'HEBREW': 'HEBREW', 'HINURD': 'HIN-URD', 'HIST': 'HIST', 'HNRS': 'HNRS', 'HUMGEN': 'HUM GEN', 'HNGAR': 'HNGAR', 'ILAMER': 'IL AMER', 'IESTD': 'I E STD', 'INDO': 'INDO', 'INFSTD': 'INF STD', 'IASTD': 'I A STD', 'INTLDV': 'INTL DV', 'IMSTD': 'I M STD', 'IRANIAN': 'IRANIAN', 'ISLMST': 'ISLM ST', 'ITALIAN': 'ITALIAN', 'JAPAN': 'JAPAN', 'JEWISH': 'JEWISH', 'KOREA': 'KOREA', 'LBRSTD': 'LBR STD', 'LATIN': 'LATIN', 'LATNAM': 'LATN AM', 'UGLAW': 'UG-LAW', 'LGBTQS': 'LGBTQS', 'LIFESCI': 'LIFESCI', 'LING': 'LING', 'LTHUAN': 'LTHUAN', 'MGMT': 'MGMT', 'MGMTEX': 'MGMTEX', 'MGMTFT': 'MGMTFT', 'MGMTFE': 'MGMTFE', 'MGMTGEX': 'MGMTGEX', 'MGMTMFE': 'MGMTMFE', 'MGMTMSA': 'MGMTMSA', 'MGMTPHD': 'MGMTPHD', 'MATSCI': 'MAT SCI', 'MATH': 'MATH', 'MECHAE': 'MECH&AE', 'MEDHIS': 'MED HIS', 'MED': 'MED', 'MIMG': 'MIMG', 'MESTD': 'M E STD', 'MILSCI': 'MIL SCI', 'MPHARM': 'M PHARM', 'MOLBIO': 'MOL BIO', 'MOLTOX': 'MOL TOX', 'MCDBIO': 'MCD BIO', 'MCIP': 'MC&IP', 'MUSC': 'MUSC', 'MSCIND': 'MSC IND', 'MUSCLG': 'MUSCLG', 'NAVSCI': 'NAV SCI', 'NREAST': 'NR EAST', 'NEURBIO': 'NEURBIO', 'NEURLGY': 'NEURLGY', 'NEUROSC': 'NEUROSC', 'NEURSGY': 'NEURSGY', 'NURSING': 'NURSING', 'NEURO':'NEURO','OBGYN': 'OBGYN', 'OPTH': 'OPTH', 'ORLBIO': 'ORL BIO', 'ORTHPDC': 'ORTHPDC', 'PATH': 'PATH', 'PEDS': 'PEDS', 'PHILOS': 'PHILOS', 'PHYSICS': 'PHYSICS', 'PBMED': 'PBMED', 'PHYSCI': 'PHYSCI', 'PHYSIOL': 'PHYSIOL', 'POLSH': 'POLSH', 'POLSCI': 'POL SCI', 'PORTGSE': 'PORTGSE', 'COMPTNG': 'COMPTNG', 'PSYCTRY': 'PSYCTRY', 'PSYCH': 'PSYCH', 'PUBAFF': 'PUB AFF', 'PUBHLT': 'PUB HLT', 'PUBPLC': 'PUB PLC', 'RADONC': 'RAD ONC', 'RELIGN': 'RELIGN', 'ROMANIA': 'ROMANIA', 'RUSSN': 'RUSSN', 'SCAND': 'SCAND', 'SCIEDU': 'SCI EDU', 'SEMITIC': 'SEMITIC', 'SRBCRO': 'SRB CRO', 'SLAVC': 'SLAVC', 'SOCSC': 'SOC SC', 'SOCTHT': 'SOC THT', 'SOCWLF': 'SOC WLF', 'SOCGEN': 'SOC GEN', 'SOCIOL': 'SOCIOL', 'SASIAN': 'S ASIAN', 'SEASIAN': 'SEASIAN', 'SPAN': 'SPAN', 'STATS': 'STATS', 'SURGERY': 'SURGERY', 'SWAHILI': 'SWAHILI', 'THAI': 'THAI', 'THEATER': 'THEATER', 'TURKIC': 'TURKIC', 'UKRN': 'UKRN', 'UNIVST': 'UNIV ST', 'URBNPL': 'URBN PL', 'UROLOGY': 'UROLOGY', 'VIETMSE': 'VIETMSE', 'WLARTS': 'WL ARTS', 'YIDDSH': 'YIDDSH'}

# stuff = []
# for subject in catalogSubjects:
#     thingy = updatedSOCGrabbing(catalogSubjects[subject])
#     if len(thingy) != 0:
#         stuff = stuff + thingy
#         with open("classdump9.json", 'w') as f:
#             json.dump(stuff, f, indent = 4)

client = MongoClient(os.environ.get("DB_URI"))
db = client["onTrackDB"]
collection = db["AllCourses"]
allCourses = []
with open('classdump5.json') as json_file:
    data = json.load(json_file)
    allCourses = data
with open('classdump6.json') as json_file:
    data = json.load(json_file)
    allCourses = allCourses + data
with open('classdump7.json') as json_file:
    data = json.load(json_file)
    allCourses = allCourses + data
with open('classdump8.json') as json_file:
    data = json.load(json_file)
    allCourses = allCourses + data
with open('classdump9.json') as json_file:
    data = json.load(json_file)
    allCourses = allCourses + data
# print(allCourses)
# uniqueNames = {}
# thing = []
# for course in allCourses:
#     print(course['Short name'])
#     if course['Short name'] not in uniqueNames:
#         uniqueNames[course['Short name']] = 0
#         thing.append(course)
# print(uniqueNames)
# print(len(thing))
# print(len(allCourses))
# collection.insert_one({"courses": allCourses})
for i in allCourses:
    collection.insert_one(i)


# print(updatedSOCGrabbing("https://catalog.registrar.ucla.edu/browse/Subject%20Areas/ARTARC"))
# client = MongoClient(os.environ.get("DB_URI"))
# db = client["onTrackDB"]
# collection = db["AllCourses"]

# collection.insert_one({"courses": stuff})

    
# dict = {}
# for subject in data:
#     properShortName = data[subject][1]
#     dict["".join(properShortName.split(" ")).replace("&","")] = properShortName
# print(dict)



# uploadAllClassesToDB()

# urls = []
# for url in SOCUrl:
#     urls.append(SOCMoreDetails(url))
#     with open('classdump4.json', 'w') as f:
#        json.dump(urls, f, indent = 4)

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
