import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

# Глобальные переменные для хранения справочников
directors_list = []
genres_list = []
languages_list = []
countries_list = []

# === Создание базы данных и таблиц ===
def create_database():
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS languages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS countries (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS genres (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS directors (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS movies (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      director_id INTEGER,
      release_year INTEGER,
      genre_id INTEGER,
      duration INTEGER,
      rating REAL,
      language_id INTEGER,
      country_id INTEGER,
      description TEXT,
      FOREIGN KEY (director_id) REFERENCES directors(id),
      FOREIGN KEY (genre_id) REFERENCES genres(id),
      FOREIGN KEY (language_id) REFERENCES languages(id),
      FOREIGN KEY (country_id) REFERENCES countries(id)
    );
    """)

    # Заполнение справочников начальными данными, если пусто
    def insert_if_empty(table, values):
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(f"INSERT INTO {table} (name) VALUES (?)", [(v,) for v in values])

    insert_if_empty('languages', ['English', 'Estonian', 'Russian'])
    insert_if_empty('countries', ['USA', 'UK', 'Estonia'])
    insert_if_empty('genres', ['Drama', 'Sci-Fi', 'Crime'])
    insert_if_empty('directors', ['Francis Ford Coppola', 'Christopher Nolan', 'Quentin Tarantino'])

    conn.commit()
    conn.close()

# === Загрузка справочников в глобальные списки ===
def load_reference_data():
    global directors_list, genres_list, languages_list, countries_list
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM directors ORDER BY name")
    directors_list = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name FROM genres ORDER BY name")
    genres_list = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name FROM languages ORDER BY name")
    languages_list = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name FROM countries ORDER BY name")
    countries_list = [row[0] for row in cursor.fetchall()]

    conn.close()

# === Загрузка фильмов в таблицу ===
def load_data(tree, search=""):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    query = """
    SELECT movies.id, movies.title, directors.name, movies.release_year, genres.name, movies.duration,
           movies.rating, languages.name, countries.name, movies.description
    FROM movies
    LEFT JOIN directors ON movies.director_id = directors.id
    LEFT JOIN genres ON movies.genre_id = genres.id
    LEFT JOIN languages ON movies.language_id = languages.id
    LEFT JOIN countries ON movies.country_id = countries.id
    """
    params = ()
    if search:
        query += " WHERE movies.title LIKE ?"
        params = ('%' + search + '%',)
    cursor.execute(query, params)

    rows = cursor.fetchall()
    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert("", "end", values=row[1:], iid=row[0])
    conn.close()

# === Получение id по имени или создание записи в справочнике ===
def get_or_create_id(table, name):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT id FROM {table} WHERE name=?", (name,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]
    cursor.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

# === Валидация данных ===
def validate_input(entries):
    title = entries["Pealkiri"].get().strip()
    year = entries["Aasta"].get().strip()
    rating = entries["Reiting"].get().strip()
    duration = entries["Kestus"].get().strip()

    if not title:
        messagebox.showerror("Viga", "Nimi on nõutav.")
        return False
    if not year.isdigit():
        messagebox.showerror("Viga", "Aasta peab olema number.")
        return False
    if duration and not duration.isdigit():
        messagebox.showerror("Viga", "Kestus peab olema number.")
        return False
    if rating:
        try:
            val = float(rating)
            if val < 0 or val > 10:
                raise ValueError()
        except:
            messagebox.showerror("Viga", "Hinnang peab olema arv vahemikus 0 kuni 10.")
            return False
    return True

# === Добавление нового фильма ===
def insert_movie(entries, win):
    if not validate_input(entries):
        return
    title = entries["Pealkiri"].get().strip()
    director = entries["Režissöör"].get()
    year = entries["Aasta"].get().strip()
    genre = entries["Žanr"].get()
    duration = entries["Kestus"].get().strip()
    rating = entries["Reiting"].get().strip()
    language = entries["Keel"].get()
    country = entries["Riik"].get()
    description = entries["Kirjeldus"].get().strip()

    director_id = get_or_create_id("directors", director)
    genre_id = get_or_create_id("genres", genre)
    language_id = get_or_create_id("languages", language)
    country_id = get_or_create_id("countries", country)

    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO movies (title, director_id, release_year, genre_id, duration, rating, language_id, country_id, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, director_id, int(year), genre_id, int(duration) if duration else None, float(rating) if rating else None, language_id, country_id, description))

    conn.commit()
    conn.close()
    messagebox.showinfo("Õnnestus", "Film lisatud.")
    win.destroy()
    load_reference_data()
    load_data(tree)

# === Окно добавления фильма ===
def open_add_window():
    win = tk.Toplevel(root)
    win.title("Lisa film")   
    entries = {}
    labels = ["Pealkiri", "Režissöör", "Aasta", "Žanr", "Kestus", "Reiting", "Keel", "Riik", "Kirjeldus"]

    for i, label in enumerate(labels):
        tk.Label(win, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=5)

        if label in ["Režissöör", "Žanr", "Keel", "Riik"]:
            cb_values = []
            if label == "Režissöör":
                cb_values = directors_list
            elif label == "Žanr":
                cb_values = genres_list
            elif label == "Keel":
                cb_values = languages_list
            elif label == "Riik":
                cb_values = countries_list
            combobox = ttk.Combobox(win, values=cb_values, state="readonly")
            if cb_values:
                combobox.current(0)
            combobox.grid(row=i, column=1, padx=10, pady=5)
            entries[label] = combobox
        else:
            entry = tk.Entry(win, width=40)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries[label] = entry

    tk.Button(win, text="Lisa", command=lambda: insert_movie(entries, win)).grid(row=len(labels), column=0, columnspan=2, pady=10)

# === Обновление фильма ===
def update_movie(record_id, entries, win):
    if not validate_input(entries):
        return
    title = entries["Pealkiri"].get().strip()
    director = entries["Režissöör"].get()
    year = entries["Aasta"].get().strip()
    genre = entries["Žanr"].get()
    duration = entries["Kestus"].get().strip()
    rating = entries["Reiting"].get().strip()
    language = entries["Keel"].get()
    country = entries["Riik"].get()
    description = entries["Kirjeldus"].get().strip()

    director_id = get_or_create_id("directors", director)
    genre_id = get_or_create_id("genres", genre)
    language_id = get_or_create_id("languages", language)
    country_id = get_or_create_id("countries", country)

    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE movies SET title=?, director_id=?, release_year=?, genre_id=?, duration=?, rating=?, language_id=?, country_id=?, description=?
        WHERE id=?
    """, (title, director_id, int(year), genre_id, int(duration) if duration else None, float(rating) if rating else None, language_id, country_id, description, record_id))

    conn.commit()
    conn.close()

    messagebox.showinfo("Edu", "Andmed uuendatud.")
    win.destroy()
    load_reference_data()
    load_data(tree)

# === Окно редактирования фильма ===
def open_edit_window():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Tähelepanu", "Valige muutmiseks kirje.")
        return
    record_id = selected[0]

    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    cursor.execute("""
    SELECT movies.title, directors.name, movies.release_year, genres.name, movies.duration,
           movies.rating, languages.name, countries.name, movies.description
    FROM movies
    LEFT JOIN directors ON movies.director_id = directors.id
    LEFT JOIN genres ON movies.genre_id = genres.id
    LEFT JOIN languages ON movies.language_id = languages.id
    LEFT JOIN countries ON movies.country_id = countries.id
    WHERE movies.id=?
    """, (record_id,))

    record = cursor.fetchone()
    conn.close()

    if not record:
        messagebox.showerror("Viga", "Kirjet ei leitud.")
        return

    win = tk.Toplevel(root)
    win.title("Redigeeri filmi")
    entries = {}

    labels = ["Pealkiri", "Režissöör", "Aasta", "Žanr", "Kestus", "Reiting", "Keel", "Riik", "Kirjeldus"]

    for i, label in enumerate(labels):
        tk.Label(win, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=5)

        if label in ["Režissöör", "Žanr", "Keel", "Riik"]:
            cb_values = []
            if label == "Režissöör":
                cb_values = directors_list
            elif label == "Žanr":
                cb_values = genres_list
            elif label == "Keel":
                cb_values = languages_list
            elif label == "Riik":
                cb_values = countries_list
            combobox = ttk.Combobox(win, values=cb_values, state="readonly")
            try:
                idx = cb_values.index(record[i])
            except ValueError:
                idx = 0
            combobox.current(idx if cb_values else 0)
            combobox.grid(row=i, column=1, padx=10, pady=5)
            entries[label] = combobox
        else:
            entry = tk.Entry(win, width=40)
            if record[i] is not None:
                entry.insert(0, str(record[i]))
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries[label] = entry

    tk.Button(win, text="Salvesta", command=lambda: update_movie(record_id, entries, win)).grid(row=len(labels), column=0, columnspan=2, pady=10)

# === Удаление фильма ===
def delete_movie():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Hoiatus", "Valige kustutamiseks kirje.")
        return
    record_id = selected[0]
    if messagebox.askyesno("Kinnita", "Kas kustutada valitud kirje?"):
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM movies WHERE id=?", (record_id,))
        conn.commit()
        conn.close()
        load_data(tree)
        messagebox.showinfo("Valmis", "Kirje kustutatud.")

# === Добавление элементов в справочники ===
def add_reference_item(table_name, list_name, root_window):
    def do_add():
        val = entry.get().strip()
        if not val:
            messagebox.showerror("Viga", "Tühi väärtus pole lubatud.")
            return
        # Проверка дублирования
        if val in globals()[list_name]:
            messagebox.showwarning("Tähelepanu", f"{val} juba nimekirjas.")
            return

        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()
        try:
            cursor.execute(f"INSERT INTO {table_name} (name) VALUES (?)", (val,))
            conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror("Viga", f"{val} juba on baasis.")
            conn.close()
            return
        conn.close()

        globals()[list_name].append(val)
        globals()[list_name].sort()
        messagebox.showinfo("Õnnestus!", f"{val} lisatud {table_name}'sse.")
        entry.delete(0, tk.END)
        refresh_reference_lists()
        update_reference_lists_in_add_edit_windows()

    add_win = tk.Toplevel(root_window)
    add_win.title(f"Lisa {table_name}")
    tk.Label(add_win, text="Siseta nimi:").pack(padx=10, pady=5)
    entry = tk.Entry(add_win, width=40)
    entry.pack(padx=10, pady=5)
    tk.Button(add_win, text="Lisa", command=do_add).pack(padx=10, pady=10)

# === Обновление глобальных списков и перезагрузка таблицы ===
def refresh_reference_lists():
    load_reference_data()

# === Обновить выпадающие списки в окнах добавления и редактирования (если открыты) ===
def update_reference_lists_in_add_edit_windows():
    # В данном простом варианте не реализуем — чтобы обновлять динамически, нужно хранить ссылки на окна и виджеты.
    # Можно доработать при необходимости.
    pass

# === Окно для управления справочниками ===
# === Удаление элемента из справочника ===
def delete_reference_item(table_name, list_name, win, listbox):
    selected_indices = listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Tähelepanu", "Vali enne elemendi kustutamist.")
        return
    selected_index = selected_indices[0]
    val = listbox.get(selected_index)

    if messagebox.askyesno("Kinnitus", f"Kustuta '{val}' {table_name}'st?"):
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()
        # Удаляем элемент по имени
        try:
            cursor.execute(f"DELETE FROM {table_name} WHERE name=?", (val,))
            conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror("Viga", f"Ei saa kustuta'{val}', sest see pole kasutamises.")
            conn.close()
            return
        conn.close()

        # Обновляем список в памяти
        globals()[list_name].remove(val)
        listbox.delete(selected_index)
        messagebox.showinfo("Õnnestus", f"'{val}' kustutatud {table_name}'st.")

        # Обновляем таблицу фильмов и справочники
        refresh_reference_lists()
        load_data(tree)

# === Lubatud andmeid===
def open_manage_reference_window():
    win = tk.Toplevel(root)
    win.title("Andmehaldus")

    # Функция создания фрейма с Listbox, кнопками Добавить и Удалить для каждого справочника
    def create_ref_section(table_name, list_name, row):
        tk.Label(win, text=table_name.capitalize()).grid(row=row*2, column=0, sticky="w", padx=10, pady=2)
        listbox = tk.Listbox(win, height=6, width=30)
        listbox.grid(row=row*2+1, column=0, padx=10, pady=2)
        # Заполнение listbox текущими значениями
        for item in globals()[list_name]:
            listbox.insert(tk.END, item)

        btn_frame = tk.Frame(win)
        btn_frame.grid(row=row*2+1, column=1, padx=5)

        btn_add = tk.Button(btn_frame, text="Lisa", width=12,
                            command=lambda: add_reference_item(table_name, list_name, win))
        btn_add.pack(pady=2)

        btn_del = tk.Button(btn_frame, text="Kustuta", width=12,
                            command=lambda: delete_reference_item(table_name, list_name, win, listbox))
        btn_del.pack(pady=2)

    create_ref_section("directors", "directors_list", 0)
    create_ref_section("genres", "genres_list", 1)
    create_ref_section("languages", "languages_list", 2)
    create_ref_section("countries", "countries_list", 3)


# === MAIN WINDOW ===
root = tk.Tk()
root.title("FilmiBAAS")

frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=10)

tk.Button(frame_buttons, text="Lisa film", command=open_add_window).grid(row=0, column=0, padx=5)
tk.Button(frame_buttons, text="Muuda filmi", command=open_edit_window).grid(row=0, column=1, padx=5)
tk.Button(frame_buttons, text="Kustuta film", command=delete_movie).grid(row=0, column=2, padx=5)
tk.Button(frame_buttons, text="Halda andmeid ", command=open_manage_reference_window).grid(row=0, column=3, padx=5)


# Поиск
search_var = tk.StringVar()
tk.Label(root, text="Otsi:").pack()
search_entry = tk.Entry(root, textvariable=search_var, width=50)
search_entry.pack()

def on_search_change(*args):
    load_data(tree, search_var.get())

search_var.trace_add('write', on_search_change)

# Таблица с фильмами
columns = ["Pealkiri", "Režissöör", "Aasta", "Žanr", "Kestus", "Reiting", "Keel", "Riik", "Kirjeldus"]
tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=100)
tree.pack(expand=True, fill=tk.BOTH, pady=10)

# Инициализация
create_database()
load_reference_data()
load_data(tree)

root.mainloop()
