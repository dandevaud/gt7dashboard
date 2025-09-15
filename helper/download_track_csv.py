import urllib.request

url = 'https://raw.githubusercontent.com/ddm999/gt7info/web-new/_data/db//course.csv'
filename = 'db/course.csv'

urllib.request.urlretrieve(url, filename)
