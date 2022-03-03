#!/usr/local/bin/python3
# pip install webdriver-manager
import os
from os.path import join, dirname
import re
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient
import time

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
client = MongoClient(os.environ.get("DB_URI"))

DEBUG = False
isHenry = True

def cleanData(data):
    if (data == None): return ""
    return (data.strip()).replace("<wbr>", "")

def getPageData(courses):
    if DEBUG: print("----------------------------New page---------------------------")
     # Gets all courses on page
    allCourseData = []
    for course in courses:
        lectures = course.find_elements(By.CLASS_NAME, "primary-row")
        courseObj = getClassData(lectures[0].find_element(By.TAG_NAME, "a").get_attribute("href"))
        allLectureData = []
        for lecture in lectures:
            lectureName = lecture.find_element(By.TAG_NAME, "a").get_attribute("innerHTML")
            days = lecture.find_elements(By.CSS_SELECTOR, ".dayColumn > div > p > *")
            
            if (len(days) == 0):
                days = ""
            else:
                days = lecture.find_element(By.TAG_NAME, "button").get_attribute("data-content")

            time = lecture.find_element(By.CSS_SELECTOR, ".timeColumn > p").get_attribute("innerHTML")

            location = lecture.find_element(By.CLASS_NAME, "locationColumn").find_element(By.TAG_NAME, "p").get_attribute("innerHTML")
            if ("button" in location):
                location = lecture.find_element(By.CSS_SELECTOR, ".locationColumn > p > button").get_attribute("innerHTML")
            professor = lecture.find_element(By.CLASS_NAME, "instructorColumn").find_element(By.TAG_NAME, "p").get_attribute("innerHTML")
            discussionsData = []
            
            discussions = lecture.find_elements(By.CLASS_NAME, "secondary-row")
            for discussion in discussions:
                discussionName = discussion.find_element(By.TAG_NAME, "a").get_attribute("innerHTML")
                days = discussion.find_elements(By.CSS_SELECTOR, ".dayColumn > div > p > *")
            
                if (len(days) == 0):
                    days = ""
                else:
                    days = discussion.find_element(By.TAG_NAME, "button").get_attribute("data-content")

                time = discussion.find_element(By.CSS_SELECTOR, ".timeColumn > p").get_attribute("innerHTML")
                location = discussion.find_element(By.CLASS_NAME, "locationColumn").find_element(By.TAG_NAME, "p").get_attribute("innerHTML")
                if ("button" in location):
                    location = discussion.find_element(By.CSS_SELECTOR, ".locationColumn > p > button").get_attribute("innerHTML")
                instructor = discussion.find_element(By.CLASS_NAME, "instructorColumn").find_element(By.TAG_NAME, "p").get_attribute("innerHTML")
                discussionsData.append({"section": cleanData(discussionName), "days": cleanData(days), "time": cleanData(time), "location": cleanData(location).replace("\n", ""), "instructor": cleanData(instructor)})
            
            lectureData = {"section": cleanData(lectureName), "professor": cleanData(professor), "location": cleanData(location).replace("\n", ""), "time": cleanData(time), "days": cleanData(days), "discussions": discussionsData}
            allLectureData.append(lectureData)

        courseObj["lectures"] = allLectureData
        allCourseData.append(courseObj)
    return allCourseData

    
def SOCgetAllClassData(url):
    if DEBUG: 
        print("----------------------------New subject area---------------------------")
        print(url)
     # Selenium config
    options = Options()
    options.headless = not DEBUG
    s = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=options, service=s)
    driver.get(url)
    html = driver.execute_script('''return document.querySelector("ucla-sa-soc-app").shadowRoot.getElementById("divSearchResults")''')
    numPages = len(html.find_elements(By.CSS_SELECTOR, '#divPagination > div:nth-child(2) > ul > li > button'))
    i = 1
    
    wait = WebDriverWait(html, 10)
    showAllClasses = wait.until(EC.presence_of_element_located((By.ID, 'expandAll')))
    showAllClasses.click()
    
    client = MongoClient(os.environ.get("DB_URI"))
    db = client["onTrackDB"]
    collection = db["CoursesOfferedS22"]

    time.sleep(2)

    courses = html.find_elements(By.CLASS_NAME, "primarySection")
    pageData = getPageData(courses)
    if not DEBUG: collection.insert_many(pageData)
    
    while (numPages > 0):
        numPages -= 1
        i += 1
        html.find_element(By.CSS_SELECTOR, '#divPagination > div:nth-child(2) > ul > li:nth-child({}) > button'.format(i)).click()

        wait = WebDriverWait(html, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'results')))
        showAllClasses.click()
        showAllClasses.click()

        WebDriverWait(html, 100).until(EC.presence_of_element_located((By.CLASS_NAME, 'primarySection')))
        time.sleep(2)
        courses = html.find_elements(By.CLASS_NAME, "primarySection")
        pageData = getPageData(courses)
        if not DEBUG: collection.insert_many(pageData)

    driver.close()
    

# TODO: Comment this, so it makes sense and is not a mess
def getClassData(link):
    if DEBUG: print("\n ----------------------------New class---------------------------")
    # Selenium config
    s = Service(ChromeDriverManager().install())
    options = Options()
    options.headless = not DEBUG
    driver = webdriver.Chrome(service=s, options=options)
    driver.get(link)

    # get innermost element that still contains all the data.
    html = driver.execute_script('''return document.querySelector("ucla-sa-soc-app").shadowRoot.getElementById("class_detail")''')
    # grab all the important info
    subject = html.find_element(By.ID, "subject_class").get_attribute('innerHTML')
    description = html.find_element(By.ID, "section").text
    description = description[:description.find("Department")]
    courseCode = (subject.split("<br>")[1]).split("</p>")[0]
    courseCode = " ".join(courseCode.split())
    fullName = courseCode.split("-")[1].lstrip()
    abbreviation = " ".join(courseCode.split("-")[0].split()[:-1])
    courseCode = courseCode.split(" - ")[0]
    if DEBUG: print(courseCode)
    
    subjectArea = subject[4:subject.find("(") - 1]
    if("<br>" in subjectArea):
        subjectArea = subjectArea.split("<br>")[0]
    restrictions = html.find_elements(By.CLASS_NAME, "enrollment_info")[1].find_elements(By.TAG_NAME, "td")[1].text
    units = html.find_elements(By.CLASS_NAME, "enrl_mtng_info")[1].find_elements(By.TAG_NAME, "td")[5].text
    requisites = ""
    if (html.find_element(By.ID, "course_requisites").text != ""):
        requisites = html.find_elements(By.CLASS_NAME, "course_requisites")

    currentQuarter = link[link.find("term_cd") + 8:link.find("term_cd") + 11]
    enforcedPrereqs = []
    enforcedCoreqs = []
    currOption = []
    cleanRequisite = ""

    for i, val in enumerate(requisites[1:]):
        requisite = val.find_element(By.CLASS_NAME, "popover-right").text.lstrip().rstrip()
        data = val.find_elements(By.TAG_NAME, "td")
        isPrereq = data[2].text == "Yes"
        isCoreq = data[3].text == "Yes"

        isAndAtEnd = requisite[-3:] == "and"
        isOrAtEnd = requisite[-2:] == "or"
        cleanRequisite = requisite.replace("(", "").replace(")", "").lstrip().rstrip()
        cleanRequisite = cleanRequisite[:-3] if isAndAtEnd else cleanRequisite[:-2] if isOrAtEnd else cleanRequisite

        numBrackets = requisite.count("(")
        if (numBrackets > 1):
            raise Exception("Bruh we get trolled by UCLA")
        if isCoreq:
            enforcedCoreqs.append(cleanRequisite)
        elif isPrereq:
            if isOrAtEnd or isAndAtEnd:
                currOption.append(cleanRequisite)
                if isAndAtEnd:
                    enforcedPrereqs.append(currOption)
                    currOption = []
                print(currOption)
            else:
                enforcedPrereqs.append([cleanRequisite])

    # add all the objects to our overall class object and return it to the calling function.
    Class = {"name": courseCode, "longName": fullName, "subjectArea": subjectArea, "subjectAreaAbbreviation": abbreviation, "quarterOffered": currentQuarter, "units": units, "enforcedPrerequisites": enforcedPrereqs, "enforcedCorequisites": enforcedCoreqs, "description": description, "restrictions": restrictions}
    if DEBUG: print(Class)
    driver.close()
    return Class

SOCUrl = ['https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=AERO+ST', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=AF+AMER', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=AFRC+ST', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=AM+IND', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ASL', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=AN+N+EA', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ANES', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ANTHRO', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=APPLING', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ARABIC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ARCHEOL', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ARCH%26UD', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ARMENIA', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ART', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ART+HIS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ART%26ARC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ARTS+ED', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ASIAN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ASIA+AM', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ASTR', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=A%26O+SCI', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=BIOENGR', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=BIOINFO', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=Undergraduate', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=BIOL+CH', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=BIOMATH', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=BMD+RES', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=BIOSTAT', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=BULGR', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=C%26EE+ST', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=CH+ENGR', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=CHEM', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=CCAS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=CHIN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=C%26EE', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=CLASSIC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=CLUSTER', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=COMM', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=CESC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=COM+HLT', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=COM+LIT', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=C&S+BIO', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=COM+SCI', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=CLT+HTG', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=CZCH', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=DANCE', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=DENT', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=DESMA', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=DGT+HUM', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=DIS+STD', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=DUTCH', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=EPS+SCI', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=EA+STDS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=EE+BIOL', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ECON', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=EDUC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=EC+ENGR', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ENGR', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ENGL', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ESL', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ENGCOMP', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ENVIRON', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ENV+HLT', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=EPIDEM', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ETHNMUS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ELTS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=FAM+MED', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=FILIPNO', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=FILM+TV', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=FOOD+ST', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=FRNCH', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=GENDER', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=GEOG', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=GERMAN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=GRNTLGY', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=GLB+HLT', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=GJ+STDS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=GLBL+ST', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=GRAD+PD', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=GREEK', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=HLT+POL', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=HLT+ADM', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=HEBREW', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=HIN-URD', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=HIST', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=HNRS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=HUM+GEN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=HNGAR', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=IL+AMER', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=I+E+STD', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=INDO', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=INF+STD', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=I+A+STD', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=INTL+DV', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=I+M+STD', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=IRANIAN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ISLM+ST', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ITALIAN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=JAPAN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=JEWISH', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=KOREA', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=LBR+STD', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=LATIN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=LATN+AM', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=LAW', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=UG-LAW', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=LGBTQS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=LIFESCI', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=LING', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=LTHUAN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MGMT', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MGMTEX', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MGMTFT', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MGMTFE', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MGMTGEX', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MGMTMFE', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MGMTMSA', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MGMTPHD', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MAT+SCI', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MATH', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MECH%26AE', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MED+HIS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MED', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MIMG', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=M+E+STD', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MIL+SCI', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=M+PHARM', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MOL+BIO', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MOL+TOX', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MCD+BIO', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MC%26IP', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MUSC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MSC+IND', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=MUSCLG', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=NAV+SCI', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=NR+EAST', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=NEURBIO', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=NEURLGY', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=NEUROSC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=NEURO++', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=NEURSGY', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=NURSING', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=OBGYN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=OPTH', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ORL+BIO', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ORTHPDC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PATH', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PEDS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PHILOS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PHYSICS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PBMED', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PHYSCI', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PHYSIOL', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=POLSH', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=POL+SCI', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PORTGSE', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=COMPTNG', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PSYCTRY', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PSYCH', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PUB+AFF', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PUB+HLT', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=PUB+PLC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=RAD+ONC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=RELIGN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ROMANIA', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=RUSSN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SCAND', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SCI+EDU', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SEMITIC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SRB+CRO', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SLAVC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SOC+SC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SOC+THT', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SOC+WLF', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SOC+GEN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SOCIOL', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=S+ASIAN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SEASIAN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SPAN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=STATS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SURGERY', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=SWAHILI', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=THAI', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=THEATER', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=TURKIC', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=UKRN', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=UNIV+ST', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=URBN+PL', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=UROLOGY', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=VIETMSE', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=WL+ARTS', 'https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=YIDDSH']

if DEBUG:
    choice = input("Choose type [1 (one page), 2 (multi page), 3 (no brackets), 4 (brackets)]: ")
    if choice == "1":
        SOCgetAllClassData("https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=ART")
    elif choice == "2":
        SOCgetAllClassData("https://sa.ucla.edu/ro/public/soc/Results?t=22S&subj=COM+SCI")
    elif choice == "3":
        getClassData("https://sa.ucla.edu/ro/Public/SOC/Results/ClassDetail?term_cd=22S&subj_area_cd=MCD%20BIO&crs_catlg_no=0193%20%20%20%20&class_id=269861201&class_no=%20001%20%20")
    elif choice == "4":
        getClassData("https://sa.ucla.edu/ro/Public/SOC/Results/ClassDetail?term_cd=22S&subj_area_cd=MCD%20BIO&crs_catlg_no=0138%20%20%20%20&class_id=269528200&class_no=%20001%20%20")
else:
    if (isHenry):
        for url in SOCUrl[96:]:
            try:
                SOCgetAllClassData(url)
            except:
                f = open('error.txt', 'a')
                f.write(url + '\n')
                f.close()
    else:
        for url in SOCUrl[:96]:
            try:
                SOCgetAllClassData(url)
            except:
                f = open('error.txt', 'a')
                f.write(url + '\n')
                f.close()