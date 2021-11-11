#!/usr/local/bin/python3
# pip install webdriver-manager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# def getClasses():
#     s = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=s)
#     driver.get('https://registrar.ucla.edu/academics/course-descriptions')
#     driver.implicitly_wait(10)
#     links = driver.find_elements_by_css_selector(
#         'div.course-descriptions-letter > ol > li > a')
#     for link in links:
#         print(link.get_attribute('href'))
#         print(link.text)
#     driver.close()

def getSubjectAreas():
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
        print(link.get_attribute('href'))
        print(link.find_element_by_css_selector('h4').text)
    driver.close()

# This is way too complicated/over programmed soltuion for what we're doing


def getClasses():
    s = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s)
    # Using this one as an example
    driver.get('https://catalog.registrar.ucla.edu/browse/Subject%20Areas/AEROST')
    driver.implicitly_wait(20)
    # https://stackoverflow.com/questions/743164/how-to-emulate-a-do-while-loop
    # Check curr page first before advancing to next page
    do = True
    list = []
    count = 0
    while (do):
        driver.implicitly_wait(50)
        links = driver.find_elements_by_css_selector(
            'a.cs-list-item.css-1hhgbew-Links--StyledLink-Links--StyledAILink.e1t6s54p8')

        for link in links:
            try:
                url = link.get_attribute('href')
                if (url in list):
                    count += 1
                    if count == 100:
                        do = False
                    break
                list.append(url)
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
    print(list)


# def getToSOCpage():
#     s = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=s)
#     driver.get('https://sa.ucla.edu/ro/public/soc')
#     driver.implicitly_wait(20)
#     driver.find_element_by_css_selector(
#         '#IweAutocompleteContainer > input').send_keys('Testing testing')
#     driver.implicitly_wait(2000)


getSubjectAreas()
# getClasses()
# getToSOCpage()
