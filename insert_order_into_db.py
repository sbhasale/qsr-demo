import pyodbc
import json
server = 'qsr.database.windows.net'
database = 'qsr'
username = 'qsradmin'
password = 'qsrP@ssword'   
driver= '{ODBC Driver 18 for SQL Server}'

with pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
    with conn.cursor() as cursor:
        order = {"bag_no" : 2, "items" : [{"French Fries" : 1, "Soda" : 1, "Fish Sandwich" : 1, "Chicken Sandwich" : 1, "Spicy Chicken Sandwich" : 1}]}
        cursor.execute("INSERT INTO [dbo].[orders] VALUES (?)", (json.dumps(order),))
        cursor.execute("SELECT TOP (1000) * FROM [dbo].[orders]")
        row = cursor.fetchone()
        while row:
            print (str(row[0]) + " " + str(row[1]))
            row = cursor.fetchone()