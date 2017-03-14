# Find Connections

A project for CMPS-263 Winter 2017: Data Driven Discovery and Visualization

The only requirements to run the server is python 3 and the data.

## Running the Server
 - Get the code: `git clone https://github.com/eriq-augustine/263-find-connections.git`
 - Move into the main directory: `cd 263-find-connections`
 - Fetch the data: Go to https://drive.google.com/file/d/0ByT1b86IZqKySjRFd0daNkxtRVE/view and download the file `pickles.tar.gz`
 - Unarchive the pickles: `tar zxf pickles.tar.gz`
 - Move the pickes into the correct directory: `mv pickles/* graph/pickles/`
 - Run the server: `python3 server.py`
 - Open up a brower and go to: http://localhost:9090/webapp

## Development Requirements
 - brotli (Decoder for the Brotli compression algorithm)
 - bs4 (Beautiful Soup 4)
 - psycopg2 (Python PostgreSQL driver)
