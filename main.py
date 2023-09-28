from db import *
import tkinter as tk
from tkinter import ttk
import ebisu
from datetime import timedelta

oneHour = timedelta(hours=1)

cards = load_cards()
logs = load_logs()

for card_id in logs:
    logs[card_id] = sorted(logs[card_id], key=lambda x: x.date)
    

def generate_id():
    for i in range(1, len(cards.keys()) + 1):
        if str(i) not in cards:
            return str(i)
    return str(len(cards.keys()) + 1)

_col, _reverse = 'id', False 
def treeview_sort_column(tv, col, reverse = False):
    global _col, _reverse
    _col, _reverse = col, reverse
    def _process_col_item(k):
        if (col == 'id'):
            return (float(tv.set(k, col)), k)
        if (col == 'recall'):
            return (float(tv.set(k, col).replace('%', '')), k)
    l = [_process_col_item(k) for k in tv.get_children('')]
    l.sort(reverse=reverse)
    # rearrange items in sorted positions
    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)
    # reverse sort next time
    def _sort():
        return treeview_sort_column(tv, col, not reverse)
    tv.heading(col, command=_sort)
               

def predict_recall(card):
    if not len(logs[card.id]):
        return 0.0
    lastLog = logs[card.id][-1]

    return ebisu.predictRecall(tuple(lastLog.model), 
            (datetime.now() - lastLog.date) / oneHour,
            exact=True)

def save_cards_and_logs():
    save_cards(cards.values())
    _logs = []
    for card in logs:
        _logs += logs[card]
    save_logs(_logs)

def select_next(window):
    card = sorted(cards.values(), key=lambda x: x.recall)[0]
    show_progress_window(window, card)

def edit_card(window: "MainWindow", card=None):
    
    if card is None:
        card = Card(generate_id())
    
    top2 = tk.Toplevel()  
    top2.geometry("500x500")

    id = tk.StringVar()
    id.set(card.id)
    
    type_var = tk.StringVar()
    type_var.set(card._type)
    
    frame1 = tk.Frame(top2)
    frame1.pack()
    label2 = tk.Label(frame1, text=f"ID: ")
    id_entry = tk.Entry(frame1, textvariable=id)
    label2.pack(side='left')
    id_entry.pack(side='left')
    
    frame1 = tk.Frame(top2)
    frame1.pack()
    label2 = tk.Label(frame1, text=f"Type: ")
    type_entry = tk.Entry(frame1, textvariable=type_var)
    label2.pack(side='left')
    type_entry.pack(side='left')



    frame2=tk.Frame(top2, width=490, height=300)
    frame2.pack()
    label2 = tk.Label(frame2, text=f"Content: ")
    label2.place(x=10, y=10)
    tbox1 = tk.Text(frame2)
    tbox1.insert('1.0', card.content)
    tbox1.place(x=10, y=45, height=200, width=500)

    def _save_card():
        _id = id.get()
        _type = type_entry.get()
        content = tbox1.get('1.0', tk.END)
        
        if not _id or not _type or not content:
            return
        
        if card.id not in cards:
            cards[_id] = Card(_id, _type, content, [])
            logs[_id] = [Log(_id, datetime.now(), (4., 4., 24.), 1)]
        else:
            _old_id = card.id
            card.id = _id
            card._type = _type
            card.content = content

            if _old_id != _id:
                cards.pop(_old_id, None) 
                cards[_id] = card
                _logs = logs[_old_id]
                for log in _logs:
                    log.card_id = _id
                logs.pop(_old_id, None)
                logs[_id] = _logs
                
        window.draw_types_menu()
        window.insert_rows()
         
        top2.destroy()

    save = tk.Button(top2, text="Save", command=_save_card)
    save.pack(side='bottom')
    top2.mainloop()

def show_progress_window(window: "MainWindow", card):
        
    
    top2 = tk.Toplevel()  
    top2.title("Progress")            
    top2.geometry("300x100")


    label = tk.Label(top2, text=f"ID: {card.id}")
    frame = tk.Frame(top2)
    label2 = tk.Label(frame, text=f"Progress: ")
    # entry = tk.Entry(frame)
    slider = ttk.Scale(
       frame,
    from_=0,
    to=1,
    orient='horizontal',  # horizontal
    value=1
)
    def _submit():
        value = float(slider.get())
        if value > 1:
            value = 1
        elif value < 0:
            value = 0

        now = datetime.now()
        lastLog = logs[card.id][-1]
        model = ebisu.updateRecall(lastLog.model,
                            value,
                            1,
                            (now - lastLog.date) / oneHour)
        logs[card.id].append(Log(card_id, now, model, value))
        cards[card.id] = card
        window.insert_rows()
        top2.destroy()
    btn = tk.Button(top2, text="Submit", command=_submit)
    
    label.pack()
    frame.pack()
    label2.pack(side='left')
    slider.pack()
    btn.pack(side='bottom')

        
    top2.mainloop()

def get_all_card_types():
    types = set()
    for card in cards.values():
        types.add(card._type)
    return list(types)
class MainWindow(tk.Tk):

    def insert_rows(self):
        try:
            self.table.delete(*self.table.get_children())
        except:
            pass
        
        for card in cards.values():
            if card._type not in self.selected_types:
                continue
            card.recall = predict_recall(card)
            self.table.insert(parent='', index = 0, values = (card.id, card.content, card._type, "{:%}".format(card.recall)))

        treeview_sort_column(self.table, _col, _reverse)
    
        save_cards_and_logs()
        
    def draw_types_menu(self):
        for widget in self.types_menu_frame.winfo_children():
            widget.destroy()
            
        self.selected_types = set(get_all_card_types())
        

        tk.Label(self.types_menu_frame, text="Types:").grid(column=0, row=0)

        def _update_selection(key):
            def wrap():
                if key in self.selected_types:
                    self.selected_types.remove(key)
                else:
                    self.selected_types.add(key)
                print(self.selected_types)
                self.insert_rows()
            return wrap
        for i, key in enumerate(get_all_card_types()):
            tk.Label(self.types_menu_frame, text=f"{key}").grid(column=0, row=1 + i)
            chbx = tk.Checkbutton(self.types_menu_frame, command=_update_selection(key))
            if key in self.selected_types:
                chbx.select()
            chbx.grid(row=1 + i, column=1)

    def __init__(self):
        tk.Tk.__init__(self)
        self.geometry('600x400')
        self.title('Muse')

        upper_frame = tk.Frame(self, width=150)
        upper_frame.pack(padx=20)

        tree_frame = tk.Frame(upper_frame, width=100)
        tree_frame.pack(side='left')

        self.types_menu_frame = tk.Frame(upper_frame, width=100, height=100, border='2')
        self.types_menu_frame.pack(side='left', padx=10)
        
            
        self.draw_types_menu()
        
        self.table = ttk.Treeview(tree_frame, columns = ('id', 'content', 'type', 'recall'), show = 'headings')
        self.table.column('id', width=10)
        self.table.column('content', width=140)
        self.table.column('type', width=140)
        self.table.column('recall', width=130)

        self.table.heading('id', text = 'ID',)
        self.table.heading('content', text = 'Content')
        self.table.heading('type', text = 'Type')
        self.table.heading('recall', text = 'Recall')
        
        self.insert_rows()        
        
        treeview_sort_column(self.table, 'id')
        treeview_sort_column(self.table, 'recall')
        
        self.table.pack(fill = 'both', expand = True)
        def item_select(_):
            for i in self.table.selection():
                print(self.table.item(i)['values'])
            # self.table.item(self.table.selection())

        def delete_items(_):
            for i in self.table.selection():
                self.table.delete(i)

        def do_popup(event):
            item = self.table.identify_row(event.y)
            child=self.table.item(item)
            self.table.focus(item)
            print(child)
            
            def _progress():
                card = cards[str(child.get('values')[0])]
                show_progress_window(self, card)
            
            def _edit():
                card = cards[str(child.get('values')[0])]
                edit_card(self, card)
            
            popup = tk.Menu(self, tearoff=0)
            popup.add_command(label="Редактировать", command=_edit) # , command=next) etc...
            popup.add_command(label="Прогресс", command=_progress)
            popup.add_separator()
            # popup.add_command(label="Exit", command=lambda: self.closeWindow())


            try:
                popup.tk_popup(event.x_root, event.y_root, 0)
            finally:
                popup.grab_release()

        self.table.bind('<<TreeviewSelect>>', item_select)
        self.table.bind('<Button-3>', do_popup)
        self.table.bind('<Delete>', delete_items)
        
        
        def _select_next():
            select_next(self)
        
        def create_card():
            edit_card(self)
        
        container = tk.Frame(self, background="#ffd3d3")
        container.pack(pady=20)
        nxt_button = tk.Button(container, text="Next", command=_select_next)
        nxt_button.pack(padx=10, side='left')
        
        create_button = tk.Button(container, text="Create", command=create_card)
        create_button.pack(padx=10, side='left')
        self.mainloop()


# try:
MainWindow()
# except Exception as e:
#     print(e)
#     save_cards(cards.values())
#     save_logs(logs)
    




# self.table.insert(parent = '', index = tk.END, values = ('XXXXX', 'YYYYY', 'ZZZZZ'))

# events

# run 