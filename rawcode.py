import mysql.connector
from turtle import *
import turtle as tur
import pywhatkit as kt
import urllib.request
from PIL import Image
from datetime import datetime
tur.bgcolor("black")
tur.color('green')
style = ('Courier', 42, 'bold')
tur.write('WELCOME TO MOVIE TICKET BOOKING CENTER!!!', font=style, align='center')
tur.hideturtle()
tur.done()


global x
def display():
           print('#'*120)
           print('#'*120,"\n")
           
def admin():
    userid=input("enter your Userid")
    password=input("enter your password")
    if(userid.lower()=="admin" and password=="123"):
            print("\nChoice 1: ***NOW SHOWING*** ")
            print("Choice 2: Add New movies and info")
            print("Choice 3: Update movies")
            print("Choice 4: Delete movies")
            print("Choice 5: Add poster")
            print("choice 6: Exit")


def add():
    name = input("Enter New movie title: ")
    na=[]
    na.append(name)
    global lang
    lang=input("Enter the languages of the movie :")
    global form
    form=input("Enter the format of the movie :")
    global genre
    genre=input("Enter the Genre of the movie :")
    global date
    date=input("Enter the release date of the movie[YYYY:MM:DD]:")
    global days
    days=int(input("Enter the number of days for which you want the movie to run:"))
    q1="Insert into Admin Values('{}','{}','{}','{}','{}',{})".format(name,lang,form,genre,date,days)
    cur.execute(q1)
    con.commit()
    print ("information inserted successfully .....")
    n=na.copy()
    return n
                            
def update():
    global up
    up=input("Enter the movie which you want to update:")
    q2="select* from Admin where MovieName='{}'".format(up)
    cur.execute(q2)
    result=cur.fetchall()
    for row in result:
        print("%10s"%row[0],"%10s"%row[1],"%10s"%row[2],"%10s"%row[3],"%10s"%row[4],"%10s"%row[5])


def delete():
    global de
    de=input("Enter the movie which you want to delete:")
    q4="select* from Admin where MovieName='{}'".format(de)
    cur.execute(q4)


        
def customer():
    
               global seats
               global price
               price=0
               num=0
               
               print("Welcome to the Movie ticket booking center")
               cust_name=input("Enter  your name\n\n")
               
               while True:
                   print("Choice 1: ***NOW SHOWING***")
                   print("Choice 2: BOOK A TICKET")
                   print("Choice 3: Bill")
                   print("Choice 4: Exit")
                   choice = int(input("Enter a choice: "))

                   if (choice == 1):
                       print(" These are the list of movies in cinemas now. Please check the details carefully and proceed to book your ticket.\n")
                       cur.execute("select * from admin")
                       movielist = cur.fetchall()
                       for i in movielist:
                           print(i)
                       

                   elif (choice == 2):
                       choice1='y'
                       
                       
                       while choice1.lower()=='y':
                           select = input("\nWould you like to start booking your ticket?(yes/no)")
                           if (select.lower() == 'yes'):
                               nam=input("\nENTER THE NAME OF THE MOVIE FOR WHICH YOU WANT TO BOOK A TICKET: ")
                               namm = "select * from admin where MovieName= '{}'".format(nam)
                               cur.execute(namm)
                               print("The languages of the movie are:")
                               cur.execute("select language from admin where MovieName = '{}'".format(nam))
                               lang=cur.fetchall()
                               for i in lang:
                                   print(i)
                                   la=input("select your language:")
                                   
                               print("The genre of the movie is:")
                               cur.execute("select genre from admin where MovieName = '{}'".format(nam))
                               gen=cur.fetchall()
                               for x in gen:
                                   print(x)
                                       
                               print("The Formats of the movie are:")
                               cur.execute("select format from admin where MovieName = '{}'".format(nam))
                               form=cur.fetchall()
                               for y in form:
                                   print(y)
                                   fo = input("\nSelect the format of the movie:")
                                       
                               number=int(input("\nPlease enter the number of the seats you would like to book: "))
                               num += number
                               print("here are the available seats:")
                               print("**************************************************************************************************************")
                               print("                                  MOVIE TICKET BOOKING CENTER                                                 ")
                               print("**************************************************************************************************************")


                               print("                                        PREMIUM 1000 RS                                                       ")
                               print(" A    |22||21||20||19|   |18||17||16||15||14||13||12||11||10||09||08||07||06||05||04||03||02||01|                    ")
                               print(" B    |22||21||20||19|   |18||17||16||15||14||13||12||11||10||09||08||07||06||05||04||03||02||01|              ")
                               print(" C    |22||21||20||19|   |18||17||16||15||14||13||12||11||10||09||08||07||06||05||04||03||02||01|              ")
                               print("      -------------------------------------------------------------------------------------------------       ")
                               print("                                       EXECUTIVE 950 RS                                                       ")
                               print("      -------------------------------------------------------------------------------------------------       ")
                               print(" D    |22||21||20||19|   |18||17||16||15||14||13||12||11||10||09||08|   |07||06||05||04||03||02||01|          ")
                               print(" E    |22||21||20||19|   |18||17||16||15||14||13||12||11||10||09||08|   |07||06||05||04||03||02||01|          ")
                               print(" F    |22||21||20||19|   |18||17||16||15||14||13||12||11||10||09||08|   |07||06||05||04||03||02||01|              ")
                               print(" G    |22||21||20||19|   |18||17||16||15||14||13||12||11||10||09||08|   |07||06||05||04||03||02||01|                      ")
                               print("      ---------------------------------------------------------------------------------------------           ")
                               print(" H    |19||18||17||16|   |15||14||13||12||11||10||09||08||07||06||05|   |04||03||02||01|                      ")
                               print("      --------------------------------------------------------------------------------------------            ")
                               print("                                       NORMAL 900 RS                                                          ")
                               print("      --------------------------------------------------------------------------------------------            ")
                               print(" I    |19||18||17||16|   |15||14||13||12||11||10||09||08||07||06||05|   |04||03||02||01|                      ")
                               print(" J    |19||18||17||16|   |15||14||13||12||11||10||09||08||07||06||05|   |04||03||02||01|                      ")
                               print(" K    |19||18||17||16|   |15||14||13||12||11||10||09||08||07||06||05|   |04||03||02||01|                      ")
                               r=input("Enter the row no. in which you want to book the ticket:")
                               global row
                               row=r     
                               E= input("enter the seat numbers which you want:").split(",")
                               print(E)
                               seats=[]
                               for i in range(0,len(E)):
                                   seats.append(E[i])
                               print(seats)
                               if (row.lower()=='i')or(row.lower()=='j')or(row.lower()=='k'):
                                  price+=num*900
                               elif(row.lower()=='d')or(row.lower()=='e')or(row.lower()=='f')or(row.lower()=='g')or (row.lower()=='h'):
                                   price+=num*950
                               elif(row.lower()=='a')or(row.lower()=='b')or(row.lower()=='c'):
                                   price+=num*1000
                               now = datetime.now()
                               q2="Insert into Bill Values('{}','{}','{}','{}','{}','{}',{})".format(cust_name,nam,la,genre,fo,now,price)
                               cur.execute(q2)
                               con.commit()
                               choice1=input("Do you want to buy more tickets........if yes press y and if no press n")
                               if choice1.lower()!='y':
                                   print("Your Bill will be generated on the 'Bill' Section")
                                   break
                       for a in range(0,len(E)):
                           if (seats==E[a] and row==r):
                               print("Sorry these seats are already booked,please select another seat")
                               break    
                                   
                   elif(choice==3):
                       print("**********Bill Details**********")
                       print("Custumer Name :",cust_name)
                       print("Movie name:",nam)
                       print("Language :",la)
                       print("Format:",fo)
                       print("Genre:",genre)
                       print("Booking Date and Time:",now)
                       print("Seats",end=':')
                       if(row.lower()=='a')or(row.lower()=='b')or(row.lower()=='c'):
                           print("Premium",sep='')
                           for seats in range(0,len(E)):
                               print(row,seats,sep='',end=',')
                       elif(row.lower()=='d')or(row.lower()=='e')or(row.lower()=='f')or(row.lower()=='g')or (row.lower()=='h'):
                           print("Executive",sep='')
                           for seats in range(0,len(E)):
                               print(row,seats,sep='',end=',')
                       elif (row.lower()=='i')or(row.lower()=='j')or(row.lower()=='k'):
                           print("Normal",sep='')
                           for seats in range(0,len(E)):
                               print(row,seats,sep='',end=',')
                       print("Total amount :",price)
                        
                       cur.execute("select* from Bill")
                       data=cur.fetchall()
                       print(10*'-',"Bill",10*'-')
                       for i in data:
                           print(i,'')
                       im=Image.open(fil)
                       print(im.show())
                       
                       choice2=input("ARE you sure you want to exit........if yes press y and if no press n")
                       if(choice2=='y'):
                           continue
                       else:
                           print("Transaction page processing....")
                           print("Thank you! Please visit again")
                           break
                   elif(choice==4):
                       print("Hope to see you soon!")
                       break
                       
                   else:
                       print("Program terminating. Please run the program again")
                       output()




                       


def output():
    
    display()
    while True:
        option=int(input("""\t\tWelcome,dear user.Please enter one of the options below:

                                 1 - Admin(requires username and password)
                                 2 - customer
                                 3 - exit  """))
        if option==1:
            admin()
            choice = int(input("Enter a choice: "))
            if choice==1:
                cur.execute("select* from Admin")
                data=cur.fetchall()
                for i in data:
                    print(i,'')
                    
            elif choice==2:
                ans='y'
                while ans.lower()=='y' or ans.lower()=='yes':
                    add()
                    
                    ans=input("Do you want to add more movies?....Press y to continue or press n to exit")
                    
    
                    

            elif choice==3:
                ans='y'
                while ans.lower()=='y' or ans.lower()=='yes':
                    update()
                    ch=input('''selct the detail  which you want to update:
                                L-to change the language
                                F-to change the format
                                G-to change the genre
                                D-to change the release date
                                Days-to change the running days
                                A-to change all the details
                                              ''')
                    
                    
                    if ch.lower()=='l':
                        
                        l=input("Enter the new language of the movie:")
                        print("The Language of the Movie is successfully updated!")
                        f,g,d,da=form,genre,date,days
                        q3="update Admin set Language='{}',Format='{}',Genre='{}',Releasedate='{}',Days={} where MovieName='{}'".format(l,f,g,d,da,up)
                        cur.execute(q3)
                        con.commit()
                        
                    elif ch.lower()=='f':
                        
                        f=input("Enter the new format of the movie:")
                        print("The Format of the Movie is successfully updated!")
                        l,g,d,da=lang,genre,date,days
                        q3="update Admin set Language='{}',Format='{}',Genre='{}',Releasedate='{}',Days={} where MovieName='{}'".format(l,f,g,d,da,up)
                        cur.execute(q3)
                        con.commit()
                        
                    elif ch.lower()=='g':
                        
                        g=input("Enter the new genre of the movie:")
                        print("The Genre of the Movie is successfully updated!")
                        l,f,d,da=lang,form,date,days
                        q3="update Admin set Language='{}',Format='{}',Genre='{}',Releasedate='{}',Days={} where MovieName='{}'".format(l,f,g,d,da,up)
                        cur.execute(q3)
                        con.commit()
                        
                    elif ch.lower()=='d':
                        
                        d=input("Enter the new release date of the movie:")
                        print("The Release date of the Movie is successfully updated!")
                        l,f,g,da=lang,form,genre,days
                        q3="update Admin set Language='{}',Format='{}',Genre='{}',Releasedate='{}',Days={} where MovieName='{}'".format(l,f,g,d,da,up)
                        cur.execute(q3)
                        con.commit()
                        
                    elif ch.lower()=='days':
                        
                        da=int(input("Enter the updated number of days for which you want the movie to run:"))
                        print("The Movie running days is successfully updated!")
                        l,f,g,d=lang,form,genre,date
                        q3="update Admin set Language='{}',Format='{}',Genre='{}',Releasedate='{}',Days={} where MovieName='{}'".format(l,f,g,d,da,up)
                        cur.execute(q3)
                        con.commit()
                        
                    else:
                        l=input("Enter the new language of the movie:")
                        f=input("Enter the new format of the movie:")
                        g=input("Enter the new genre of the movie:")
                        d=input("Enter the new release date of the movie:")
                        da=int(input("Enter the updated number of days for which you want the movie to run:"))
                        q3="update Admin set Language='{}',Format='{}',Genre='{}',Releasedate='{}',Days={} where MovieName='{}'".format(l,f,g,d,da,up)
                        cur.execute(q3)
                        con.commit()
                        print("The Movie is successfully updated!")
                    ans=input("Do you want to update more movies?....Press y to continue or press n to exit")      

            elif choice==4:
                ans='y'
                while ans.lower()=='y' or ans.lower()=='yes':
                    delete()
                    q5="delete from Admin where  MovieName='{}'".format(de)
                    cur.execute(q5)
                    con.commit()
                    result=cur.fetchmany(5)
                    print(5*'*','Movie is deleted successfully!',5*'*')
                    ans=input("Do you want to delete more movies?.....Press y to continue or press n to exit")
        
            elif choice==5:
                ans='y'
                while ans.lower()=='y' or ans.lower()=='yes':
                    n=input("Enter the name of the movie for which you need to add the poster:-")
                    print("Let's perform Google search!")
                    target1 = n
                    kt.search(target1)
                    try:
                        global fil
                        lin=input("Enter the link for the poster")
                        fil=input("Enter the file name to store[movie_name.png]")
                        urllib.request.urlretrieve(lin,fil)
                        img = Image.open(fil)
                        img.show()
                       
                    except URLError():
                         print('')
                    ans=input("Do you want to add more posters?.....Press y to continue or press n to exit")
            elif choice==6:
                return output()
                
        elif option==2:
            customer()
            return output()
        elif option==3:
            print("Thank you for coming and we hope to see you again!!")
            break
            
                
con = mysql.connector.connect(host="localhost",user='root',password='admin',database="MovieTicketBooking")
cur=con.cursor(buffered=True)
cur.execute("drop table admin")
cur.execute("drop table bill")
cur.execute("create table Admin(MovieName varchar(50),Language varchar(75),Format varchar(35),Genre varchar (50),Releasedate DATE,Days int)")
cur.execute("create table Bill(CustomerName varchar(50),MovieName varchar(50),Language varchar(75),Format varchar(35),Genre varchar (50),Bookingdate DATE,Totalprice int)")
output()


    




