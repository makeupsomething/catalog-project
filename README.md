# The fourth project for the FSND by Udacity

## About
A Item Catalog, categories are displayed in the sidebar on the left. 
Users can browse categories and individual items.
Logged in users can add new items, edit existing items and delete existing items.

Some json endpoints are provided for all categories, individual categories and individual items.

## To Run

### You will need:
- Python2.7
- Vagrant
- VirtualBox

### Setup
1. Install Vagrant And VirtualBox
2. Download the supporting files
3. Clone this repository
4. Setup the database
5. Populate the database
6. Run the server

### To Run

The supporting files for this project can be found [here](https://github.com/udacity/fullstack-nanodegree-vm), inside you will find a `vagrant` folder. In the terminal `cd` to there and run the command `vagrant up` this may take a while as needs to download the preconfigured virtual machine. After that command finished run `vagrant ssh` to log into the machine. Note, you are also free to use your own virtual machine but you will need to configure it yourself.

Once you have logged into the virtual machine, clone this repository and do the following steps

Set up the databse:
```
python setup_db.py
```

Populate the databse with soe intitial values:
```
python populate.py
```

Finally, run the server:
```
python project.py
```
