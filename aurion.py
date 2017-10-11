import requests
import re
from selenium import webdriver
import time
from bs4 import BeautifulSoup
from twilio.rest import Client
import csv
import shutil
import os
from pprint import pprint
import re
import urllib.parse
import credentials

fieldnames = ['starttime', 'endtime', 'location', 'group', 'professor', 'type', 'id', 'name', 'day']

def dict_compare(d1, d2): # https://stackoverflow.com/a/18860653
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    modified = {o : (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
    same = set(o for o in intersect_keys if d1[o] == d2[o])
    return modified

def nicetext(text):
    if text == 'location':
        return 'Le lieu'
    elif text == 'starttime':
        return 'Le début du cours'
    elif text == 'endtime':
        return 'La fin du cours'
    elif text == 'group':
        return 'Le groupe'
    elif text == 'professor':
        return 'Le professeur'
    elif text == 'type':
        return 'Le type de cours'
    elif text == 'id':
        return 'Le code UE'
    elif text == 'name':
        return 'Le nom de cours'
    elif text == 'day':
        return 'Le jour de la semaine'
    else:
        return 'Valeur'

def dayoftheweek(no):
    if no == 0:
        return 'Lundi'
    elif no == 1:
        return 'Mardi'
    elif no == 2:
        return 'Mercredi'
    elif no == 3:
        return 'Jeudi'
    elif no == 4:
        return 'Vendredi'
    elif no == 5:
        return 'Samedi'

def diff(t1, t2):
    modif = []
    added = []
    removed = []
    for item1 in t1:
        y = 1
        z = 0
        if item1.get('name') == '':
            continue
        for item2 in t2:
            if item2.get('name') == '':
                continue
            if item1.get('name') == item2.get('name') and item1.get('day') == item2.get('day'):
                changed = dict_compare(item1,item2)
                modif.append((item1.get('name'), item1.get('day'), list(changed.keys())[0], list(changed.values())[0][0], list(changed.values())[0][1]))
                z = z + 1
            if y == len(t2) and z == 0: # for item1, no item2 corresponding -> item removed
                removed.append(item1)
            y = y + 1
    for item2 in t2:
        y = 1
        z = 0
        if item2.get('name') == '':
            continue
        for item1 in t1:
            if item1.get('name') == '':
                continue
            if item1.get('name') == item2.get('name') and item1.get('day') == item2.get('day') and item1.get('name') != '':
                z = z + 1
            if y == len(t1) and z == 0: # for item2, no item1 corresponding -> item added
                added.append(item2)
            y = y + 1
    result = {'values_changed': modif, 'item_added': added, 'item_removed': removed}
    return result
                

driver = webdriver.PhantomJS()
driver.set_window_size(1600, 900)
print("Loading Aurion...")
driver.get("http://aurion.ensait.fr")
time.sleep(2)
loginfield = driver.find_element_by_id("j_username")
loginfield.send_keys(credentials.login)
passwordfield = driver.find_element_by_id("j_password")
passwordfield.send_keys(credentials.password)
loginbutton = driver.find_element_by_id("j_idt27")
loginbutton.click()
print("Connecting...")
time.sleep(2)
planningbutton = driver.find_element_by_id('form:entree_47449')
planningbutton.click()
print("Fetching the schedule.")
time.sleep(5)
soup = BeautifulSoup(driver.page_source, "html.parser")
days = soup.select(".fc-content-skeleton > table > tbody > tr > td")
days.pop(0)
courses = [None]*6
i = 0
dayIcours = [[] for _ in range(6)]
for day in days:
    dayBS = BeautifulSoup(str(day), "html.parser")
    courses[i] = dayBS.find_all(class_='fc-title')
    cours = [None]*len(courses[i])
    j = 0
    for course in courses[i]:
        split = course.contents[0].split(' - ')
        cours[j] = {}
        cours[j]['starttime'] = split[0]
        cours[j]['endtime'] = split[1]
        cours[j]['location'] = split[2]
        cours[j]['group'] = split[3]
        cours[j]['professor'] = split[4]
        cours[j]['type'] = split[5]
        cours[j]['id'] = split[6]
        cours[j]['name'] = split[7]
        cours[j]['day'] = dayoftheweek(i)
        j = j + 1
    dayIcours[i] = cours
    i = i + 1
driver.close()
try:
    shutil.copy2('schedule.csv', 'schedule_old.csv')
except:
    pass
with open('schedule.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    k = 0
    for day in dayIcours:
        for i in range(len(day)):
            writer.writerow(dayIcours[k][i])
        k = k + 1
try:
    with open('schedule_old.csv', 'r') as oldcsvfile:
        old_list = []
        reader = csv.DictReader(oldcsvfile)
        for row in reader:
            old_list.append(row)
except FileNotFoundError:
    raise SystemExit(0) # Can't compare old vs new if there's no old file
with open('schedule.csv', 'r') as newcsvfile:
    new_list = []
    reader = csv.DictReader(newcsvfile)
    for row in reader:
        new_list.append(row)

temp3 = [x for x in new_list if x not in old_list]
temp4 = [x for x in old_list if x not in new_list]

ddiff = diff(temp4, temp3)
msg = []

try:
    for item in list(ddiff['values_changed']):
        print(nicetext(item[2]) + ' change de ' + item[3] + ' à ' + item[4] + ' pour le cours de ' + item[0] + ' de ' + item[1] + '.')
        msg.append(nicetext(item[2]) + ' change de ' + item[3] + ' à ' + item[4] + ' pour le cours de ' + item[0] + ' de ' + item[1] + '.')
except IndexError:
    pass

try:
    for item in list(ddiff['item_removed']):
        print('Le cours de ' + item['name'] + ' de ' + item['day'] + ' qui commençait à ' + item['starttime'] + ' et terminait à ' + item['endtime'] + ' a été supprimé.')
        msg.append('Le cours de ' + item['name'] + ' de ' + item['day'] + ' qui commençait à ' + item['starttime'] + ' et terminait à ' + item['endtime'] + ' a été supprimé.')
except IndexError:
    pass

try:
    for item in list(ddiff['item_added']):
        print(item['day'] + ', un cours de ' + item['name'] + ' a été ajouté. Il commence à ' + item['starttime'] + ', termine à ' + item['endtime'] + ' et aura lieu en ' + item['location'] + '.')
        msg.append(item['day'] + ', un cours de ' + item['name'] + ' a été ajouté. Il commence à ' + item['starttime'] + ', termine à ' + item['endtime'] + ' et aura lieu en ' + item['location'] + '.')
except IndexError:
    pass

data = {
    'user': credentials.apifreeuser,
    'pass': credentials.apifreepass,
    'msg':  '\r'.join(msg)
}
r = requests.get('https://smsapi.free-mobile.fr/sendmsg', urllib.parse.urlencode(data))
print(r.status_code)
