import os
import psycopg2
from tkinter import messagebox

conn=psycopg2.connect(
    host="localhost",
    database="smart_city_project",
    user="Muhammad_Ishaq",
    password="ishaq156",
)
cur=conn.cursor()

def delete_missing_map():
    try:
        cur.execute("SELECT map_name FROM pre_avaliable_map")
        all_map=cur.fetchall()

        delete=0

        for (map_name,) in all_map:
            filename=f"{map_name}.html"
            if not os.path.exists(filename):
                cur.execute("DELETE FROM pre_avaliable_map WHERE map_name=%s",(map_name,))
                delete+=1

        conn.commit()
        if delete > 0:
            messagebox.showinfo("Cleanup Done",f"{delete} broken maps remove from database")
        else:
            messagebox.showinfo("All Good","No missing map found . Everything is in sync")

    except Exception as e:
        conn.rollback()
        messagebox.showerror("Cleanup Error",str(e))
    
    finally:
        cur.close()
        conn.close()

if __name__=="__main__":
    delete_missing_map()