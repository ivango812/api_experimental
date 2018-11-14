# API Experiment

Implementation of simple API for scoring service.

Required `Python3`

Service url: `/method/`

Request - `json` in format:

    {
        account: <account name>
        login: <your login>
        method: <method>
        token: <token>
        arguments: <depends on method - see bellow>   
    }

Methods:

* [online_score](online_score)
* [clients_interests](clients_interests)

### Methods details
    
**online_score**

*arguments:*

    {
        phone: <string(11) or int, starts with "7">,
        email: <string>,
        fierst_name: <string>,
        last_name: <string>,
        birthday: <date in "DD.MM.YYYY" (not older then 70 years)>,
        gender: <int - 0, 1, 2>
    }

**Response**

    {"score": <int>}
    
    
**clients_interests**

*arguments:*

    {
        clilent_ids: <list of int>,
        date: <date in "DD.MM.YYYY">
    }

**Response**

    List of clients with {<client id>: list of interests}
    


### Usage

Run a server:

    python3 api.py

Write log in the file:

    python3 api.py --log=<filename>


   
### Run tests

Just run:

    python3 test.py  

### Author

**Ivan Gorban**

* [ivan@igorban.ru]()

### License

Copyright © 2018, Ivan Gorban. Released under the MIT License.