# SISNA - Sistem Standarisasi Nomenklatur APBD
SISNA merupakan aplikasi yang dibangun dengan bahasa Python dan framework FastAPI sebagai front-end dan back-end yang diintegrasikan dengan framework Dash untuk visualisasi tabel dan grafik secara dinamis. SISNA dapat digunakan untuk pengolahan data sekaligus visualisasi data.

Tujuan repository ini utamanya adalah untuk submisi Lomba Bedah Data APBD 2022 🙏 

Here the archietcture of this system of SISNA - Sistem Standarisasi Nomenklatur APBD

## Python Framework
This Repository is using FastAPI and Dash Framework. 
FastAPI is a framework that can benefit high performance, easy to learn, fast to code, ready for production.
Dash is a powerful platform that can benefit anyone that works with data. Dash Plotly is a great tool to have.

 - [FastAPI](https://fastapi.tiangolo.com/)
 - [Dash-Plotly](https://dash.plotly.com/)

## Installation in Localhost
I recommend creating python virtual environment, like this command.

    $ python -m venv venv

Then, activate the virtual environment.

    $ . venv/bin/activate
    
Then, just installing python library dependencies with this command, since you will most likely use it.

    $ pip install -r requirements.txt
    
Then, create new file .env that contains the environment variables

    $ DEBUG='', INTERVAL='', GOOGLE_CLIENT_ID='', GOOGLE_CLIENT_SECRET='', DATABASE_URL='', APIKEYAPP=''
    
Finally, you can start the SISNA application with run uvicorn server.

    $ uvicorn app.main:app --reload
    

## Installation in Heroku Cloud Platform
Just execute the Dockerfile and heroku.yml


## Demo SISNA - Sistem Standarisasi Nomenklatur APBD
![SISNA - Sistem Standarisasi Nomenklatur APBD Demo] (app/static/images/sisna-demo.gif)


[comment]: <> (This is a wonderful community of people dedicated to supporting others learning Dash. You can find me there as well under the name CharmingData.)

[comment]: <> (## Execute Code in Browser)

[comment]: <> (If you prefer to run the code of this repository directly online instead of on your computer, paste my Workspace link into your browser and follow the gif below. )

[comment]: <> (> [Workspace Snapshot]&#40;https://gitpod.io#snapshot/1c6d1667-643f-491a-a746-8a232413bd43&#41;)

[comment]: <> (![gitpod-demo]&#40;https://user-images.githubusercontent.com/32049495/167286451-f53e5e40-b5eb-4fc6-ad53-f7ca0e660942.gif&#41;)

