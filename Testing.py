import tkinter as tk
from tkinter import ttk
import csv
import numpy as np
from PIL import Image
import pandas as pd
import cv2
import os

window = tk.Tk()
window.title("Attendance")
window.geometry("1000x600")
notebook = ttk.Notebook(window)
#tab1
tab1 = ttk.Frame(notebook)
#tab2
tab2 = ttk.Frame(notebook)
notebook.add(tab1, text="Class 1")
notebook.add(tab2, text="tab2")
notebook.pack()
menu = tk.Menu(tab1)
students_file = "students.csv"
#functions
def load_students():
    if not os.path.exists(students_file):
        with open(students_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "First Name", "Last Name", "Status"])
    students = {"IDs": [], "first_names": [], "last_names": [], "status": []}
    with open(students_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            students["IDs"].append(int(row["ID"]))
            students["first_names"].append(row["First Name"])
            students["last_names"].append(row["Last Name"])
            students["status"].append(row["Status"])
    return students

def refresh_table():
    global students
    students = load_students()
    table.delete(*table.get_children())
    for i in range(len(students["first_names"])):
        first, last, status = students["first_names"][i], students["last_names"][i], students["status"][i]
        ID = students["IDs"][i]
        email = f"{first}.{last}@greenwoodcollege.com"
        data = (first, last, email, ID, status)
        table.insert("", "end", values=data)

def new_student():
    global status
    popup = tk.Toplevel(window)
    popup.title("Add New Student")
    popup.geometry("300x200")

    tk.Label(popup, text="First Name:").pack(pady=5)
    first_name_entry = tk.Entry(popup)
    first_name_entry.pack(pady=5)

    tk.Label(popup, text="Last Name:").pack(pady=5)
    last_name_entry = tk.Entry(popup)
    last_name_entry.pack(pady=5)
    def submit():
        new_first_name = first_name_entry.get()
        new_last_name = last_name_entry.get()
        status = "----"
        try:
            ID = (int(students['IDs'][-1])+1)
        except IndexError:
            ID = 0
        if new_first_name and new_last_name:
            students['first_names'].append(new_first_name)
            students['last_names'].append(new_last_name)
            students['status'].append(status)
            students['IDs'].append(ID)
            with open(students_file, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([ID, new_first_name, new_last_name, "----"])
            refresh_table()
            popup.destroy()

    submit_button = tk.Button(popup, text="Submit", command=submit)
    submit_button.pack(pady=10)


def change_status(value):
    global i
    index = table_selection(event=None)
    for i in table.selection():
        ID = table.item(i)['values'][3]
        if value == 1:
            face_status = face_recognition(ID)
            if not face_status:
                print("Face not recognized! Attendance not updated.")
                return
            student_status = "Present"
        elif value == 2:
            student_status = "Absent"
        else:
            student_status = "Late"

    column_value = table.item(i)['values']
    column_value.pop(4)
    column_value.append(student_status)
    table.item(i, values=column_value)
    students['status'][index] = student_status

def on_right_click(event):
    item_id = table.identify_row(event.y)  # Get selected row
    if item_id:
        popup = tk.Menu(tab1, tearoff=0)
        popup.add_command(label="Present", command=lambda: change_status(1))
        popup.add_command(label="Absent", command=lambda: change_status(2))
        popup.add_command(label="Late", command=lambda: change_status(3))
        popup.post(event.x_root, event.y_root)

def delete_items(_):
    selected_items = table.selection()
    if not selected_items:
        return
    selected_ids = [int(table.item(i)['values'][3]) for i in selected_items]
    updated_rows = []
    with open(students_file, 'r', newline='') as file:
        reader = csv.reader(file)
        header = next(reader, None)
        for row in reader:
            if row and len(row) > 0:
                try:
                    row_id = int(row[0])
                    if row_id not in selected_ids:
                        updated_rows.append(row)
                except ValueError:
                    print(f"Skipping row: {row}")
                    continue
    with open(students_file, 'w', newline='') as file:
        writer = csv.writer(file)
        if header:
            writer.writerow(header)
        writer.writerows(updated_rows)
    with open(students_file, 'r') as file:
        print(file.read())
    for i in selected_items:
        table.delete(i)
    refresh_table()


def table_selection(event):
    selected_item = table.selection()
    index = None
    if selected_item:
        selected_item_id = selected_item[0]
        index = table.index(selected_item_id)
    return index

def face_recognition(user_id):
    popup = tk.Toplevel(window)
    popup.title("Face recognition")
    popup.geometry("1250x900")
    popup.configure(bg="grey")
    ID = user_id
    print(ID)
    recognized = False
    # functions
    def TakeImages(user_id):
        first = first_name_entry.get().strip()
        last = last_name_entry.get().strip()
        if first.isalpha() and last.isalpha():
            file_path = "UserDetails/UserDetails.csv"
            if not os.path.exists(file_path):
                with open(file_path, 'w', newline='') as csvFile:
                    writer = csv.writer(csvFile)
                    writer.writerow(["ID", "Last Name", "First Name"])
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                print("Error reading CSV:", e)
                return
            df.columns = df.columns.str.strip()
            matching = df[(df['First Name'] == first) & (df['Last Name'] == last)]
            if not matching.empty:
                student_id = matching.iloc[0]['ID']
            else:
                student_id = user_id
                with open(file_path, 'a', newline='') as csvFile:
                    writer = csv.writer(csvFile)
                    writer.writerow([student_id, last, first])
            cam = cv2.VideoCapture(0)
            harcascadePath = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            detector = cv2.CascadeClassifier(harcascadePath)
            sampleNum = 0
            while True:
                ret, img = cam.read()
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = detector.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    sampleNum += 1
                    filename = f"TrainingImage/{student_id}.{first}.{last}.{sampleNum}.jpg"
                    cv2.imwrite(filename, gray[y:y + h, x:x + w])
                    cv2.imshow('frame', img)
                if cv2.waitKey(100) & 0xFF == ord('q'):
                    break
                elif sampleNum > 60:
                    break
            cam.release()
            cv2.destroyAllWindows()
            message.configure(text="Images Saved for Last Name: " + last + " First Name: " + first)
        else:
            message.configure(text="Invalid ID or Name")

    def TrainImages():
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        harcascadePath = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(harcascadePath)
        faces, Ids = getImagesAndLabels("TrainingImage")
        Ids = [str(id_val) for id_val in Ids]
        labels = np.array(Ids, dtype=np.int32)
        recognizer.train(faces, labels)
        recognizer.save("TrainingImageLabel/Trainer.yml")
        message.configure(text="Image Trained")

    def getImagesAndLabels(path):
        imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
        faces = []
        Ids = []
        for imagePath in imagePaths:
            pilImage = Image.open(imagePath).convert('L')
            imageNp = np.array(pilImage, 'uint8')
            Id = int(os.path.split(imagePath)[-1].split(".")[0])
            faces.append(imageNp)
            Ids.append(Id)
        return faces, Ids

    def TrackImages(user_id):
        nonlocal recognized
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read("TrainingImageLabel/Trainer.yml")
        faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        df = pd.read_csv("UserDetails/UserDetails.csv")
        df.columns = df.columns.str.strip()  # Strip extra spaces in headers
        cam = cv2.VideoCapture(0)
        while True:
            ret, im = cam.read()
            if not ret or im is None:
                print("Error: Could not capture image from camera.")

            gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(gray, 1.2, 5)
            for (x, y, w, h) in faces:
                Id, conf = recognizer.predict(gray[y:y + h, x:x + w])
                print(Id)
                print(conf)
                print(df['ID'].values)
                if conf < 70 and Id == user_id:
                    if Id in df['ID'].values:
                        matched_person = df[df["ID"] == Id]
                        if not matched_person.empty:
                            name = matched_person.iloc[0]["First Name"]
                        else:
                            print(f"Error: ID {Id} not found in CSV!")
                        print(f"Recognized: {name}")
                        cv2.putText(im, name, (x, y + h), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                        recognized = True
                        cam.release()
                        cv2.destroyAllWindows()
                        popup.destroy()
                        return
                    else:
                        print(f"Error: ID {Id} not found in CSV!")

                else:
                    cv2.putText(im, "Unknown", (x, y + h), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            cv2.imshow('Face Recognition', im)

            if cv2.waitKey(1) == ord('q'):
                break

        cam.release()
        cv2.destroyAllWindows()

    def clear_Data():
        directory = r'C:\Users\natey\PycharmProjects\Attendance\TrainingImage'
        print("Files in directory:")
        for file in os.listdir(directory):
            print(file)

        for file in os.listdir(directory):
            if file.lower().endswith(('.jpeg', '.jpg')):
                file_path = os.path.join(directory, file)
                print(f"Attempting to delete: {file_path}")
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file}")
                except Exception as e:
                    print(f"Error deleting {file}: {e}")
        file_path = r"C:\Users\natey\PycharmProjects\Attendance\UserDetails\UserDetails.csv"
        with open(file_path, 'r') as file:
            first_line = file.readline()

        with open(file_path, 'w') as file:
            file.write(first_line)

    # labels
    message = tk.Label(popup, text="Face-Recognition-System",
                       bg="green", fg="white", width=50,
                       height=3, font=('times', 30, 'bold'))
    message.place(x=20, y=20)

    lbl = tk.Label(popup, text="First Name", width=20, height=2,
                   fg="green", bg="white", font=('times', 15, ' bold '))
    lbl.place(x=350, y=200)

    first_name_entry = tk.Entry(popup, width=20, bg="white",
                          fg="green", font=('times', 15, ' bold '))
    first_name_entry.place(x=650, y=215)

    lbl2 = tk.Label(popup, text="Last Name", width=20, fg="green",
                    bg="white", height=2, font=('times', 15, ' bold '))
    lbl2.place(x=350, y=300)

    last_name_entry = tk.Entry(popup, width=20, bg="white",
                        fg="green", font=('times', 15, ' bold '))
    last_name_entry.place(x=650, y=315)

    # buttons
    takeImg = tk.Button(
        popup, text="Take Images",
        command=lambda:TakeImages(ID), fg="white", bg="blue",
        width=20, height=3, activebackground="Red",
        font=('times', 15, ' bold ')
    )
    takeImg.place(x=50, y=500)

    trainImg = tk.Button(
        popup, text="Train Images",
        command=TrainImages, fg="white", bg="blue",
        width=20, height=3, activebackground="Red",
        font=('times', 15, ' bold ')
    )
    trainImg.place(x=350, y=500)

    trackImg = tk.Button(
        popup, text="Recognize Faces",
        command=lambda:TrackImages(ID), fg="white", bg="blue",
        width=20, height=3, activebackground="Red",
        font=('times', 15, ' bold ')
    )
    trackImg.place(x=650, y=500)

    quitWindow = tk.Button(
        popup, text="Quit",
        command=popup.destroy, fg="white", bg="red",
        width=20, height=3, activebackground="Red",
        font=('times', 15, ' bold ')
    )
    quitWindow.place(x=950, y=500)

    clearData = tk.Button(
        popup, text="Clear Data",
        command=clear_Data, fg="white", bg="red",
        width=20, height=3, activebackground="Red",
        font=('times', 15, ' bold ')
    )
    clearData.place(x=650, y=600)

    popup.wait_window()
    return recognized

def change_Name():
    directory = r"C:\Users\natey\PycharmProjects\Attendance\TrainingImage"
    for filename in os.listdir(directory):
        if filename.startswith("4") and filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            old_path = os.path.join(directory, filename)
            new_name = "6" + filename[1:]
            new_path = os.path.join(directory, new_name)

            # Rename the file
            os.rename(old_path, new_path)
            print(f"Renamed: {filename} → {new_name}")

    print("Renaming complete!")

#data
students = load_students()
#table
table = ttk.Treeview(tab1, columns= ('first', 'last', 'email', 'id', 'attending'), show = "headings")
table.heading('first', text = 'First Name')
table.heading('last', text = 'Last Name')
table.heading('email', text = 'Email')
table.heading('id', text = 'ID')
table.heading('attending', text = 'Attending')
table.pack(fill = 'both', expand = True)

#inputing data
x = 0
y = 0
for i in range(len(students['first_names'])):
    first = students["first_names"][x]
    last = students["last_names"][y]
    email = f'{first}.{last}@greenwoodcollege.com'
    status = students["status"][x]
    IDs = students["IDs"][x]
    data = (first,last,email,IDs,status)
    table.insert(parent = "", index = 0, values = data)
    x += 1
    y += 1

refresh_table()
#submenu
file_menu = tk.Menu(menu, tearoff = False)
file_menu.add_command(label = "New", command = lambda: new_student())
menu.add_cascade(label = "File", menu = file_menu)

quit_menu = tk.Menu(menu, tearoff = False)
quit_menu.add_command(label = "Quit", command = window.destroy)
menu.add_cascade(label = "Quit", menu = quit_menu)

window.config(menu = menu)

table.bind("<Button-3>", on_right_click)
table.bind("<Delete>", delete_items)
table.bind("<<TreeviewSelect>>", table_selection)

window.mainloop()
