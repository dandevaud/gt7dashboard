FROM python:3.12

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ADD https://raw.githubusercontent.com/ddm999/gt7info/web-new/_data/db/cars.csv db/cars.csv
ADD https://raw.githubusercontent.com/ddm999/gt7info/web-new/_data/db/course.csv db/course.csv
RUN chmod -R 755 db
RUN chmod +x ./runProcess.sh

CMD [ "./runProcess.sh" ]
