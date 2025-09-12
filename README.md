This project seeks to explore compression, streaming and analyzing data over http.
To run the python client which gathers camera frames
### Running the client
```
cd client
python client.py
```
### Running the server
first you need to build the react with vite
```
cd client/vite
npm install
npm run build
```
then start the server
```
cd server
python server.py
```