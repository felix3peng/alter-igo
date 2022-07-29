# imports
import os
import sys
import numpy as np
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
import matplotlib.pyplot as plt
import matplotlib_venn as v
import seaborn as sns
import openai
openai.api_key = os.getenv('OPENAI_API_KEY')
import shap
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from io import StringIO, BytesIO
from datetime import datetime
from PIL import Image
import re
import base64
import traceback
import time
from flask_login import current_user
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

from .models import db, User, Log, CodeEdit

'''
VARIABLE DEFINITIONS
'''
s00 = '''import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns'''
s01 = '''pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)'''

codex_context = '# import standard libraries\n' + s00 + '\n'
fname = 'codex_script_' + re.sub('\.[0-9]+', '', str(datetime.now()).replace(' ', '_').replace(':', '_')) + '.txt'
codex_filename = os.path.join(os.getcwd(), 'codex_logs', fname)

error_msg = 'Sorry, something went wrong. Please check the code and edit as needed.'


'''
FUNCTION DEFINITIONS
'''
# submit codex API call for single-line command
def codex_call(prompt):
    # time the api response
    start = time.time()
    # template for openai codex api request
    response = openai.Completion.create(
        model="code-davinci-002",
        prompt=prompt,
        temperature=0,
        max_tokens=4000,
        frequency_penalty=1,
        presence_penalty=1,
        stop=["#", "'''", '"""']
        )
    end = time.time()
    elapsed = end - start
    return response['choices'][0]['text'], elapsed


# submit codex API call for multi-line command (without # as stop sequence)
def codex_call_multiline(prompt):
    # time the api response
    start = time.time()
    # template for openai codex api request
    response = openai.Completion.create(
        model="code-davinci-002",
        prompt=prompt,
        temperature=0,
        max_tokens=4000,
        frequency_penalty=1,
        presence_penalty=1,
        stop=["'''", '"""']
        )
    end = time.time()
    elapsed = end - start
    return response['choices'][0]['text'], elapsed


# mini-function to trim codex_context when necessary
def trim_prompt(prompt):
    if len(prompt) > 2000:
        print('Codex prompt is getting too long! Trimming...')
        # identify positions of each inline comment prompt
        command_positions = [(m.start(), m.end()) for m in re.finditer('#.+', prompt)]
        # identify positions of each block comment prompt
        block_key_positions = [(m.start(), m.end()) for m in re.finditer("'''.+'''", prompt)]
        # logic: if block comments exist, check whether the most recent command is inline or block
        # trim to the most recent command
        # otherwise, trim to the most recent inline comment
        if len(block_key_positions) > 0:
            if command_positions[-1][0] > block_key_positions[-1][0]:
                prompt = prompt[command_positions[-1][0]:]
            else:
                prompt = prompt[block_key_positions[-1][0]:]
        else:
            prompt = prompt[command_positions[-1][0]:]
    return prompt

# run a code string snippet and return the output
def runcode(code, ldict, old_stdout, numtables, numplots):
    global error_msg
    # make a copy of ldict to avoid changing the original (in case of error)
    tldict = ldict.copy()
    # turn off plotting to save memory
    plt.ioff()
    try:
        exec(code, tldict)
    except KeyError:
        pass
    except:
        print(error_msg + '\nTraceback:\n' + traceback.format_exc())
    # capture output of code as a figure and extract data
    fig = plt.gcf()
    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close()
    p = Image.open(buf)
    x = np.array(p.getdata(), dtype=np.uint8).reshape(p.size[1], p.size[0], -1)
    # if min and max colors are the same, it wasn't a plot - re-run as string
    if np.min(x) == np.max(x):
        new_stdout = StringIO()
        sys.stdout = new_stdout
        try:
            exec(code, ldict)
        except KeyError:
            pass
        except:
            print(error_msg + '\nTraceback:\n' + traceback.format_exc())
        output = new_stdout.getvalue()
        sys.stdout = old_stdout

        # further parsing to determine if plain string or dataframe
        if bool(re.search('Index', output)):
            outputtype = 'string'
        elif bool(re.search('Traceback', output)):
            outputtype = 'string'
        elif bool(re.search(r'[\s]{3,}', output)):
            outputtype = 'dataframe'
            headers = re.split('\s+', output.partition('\n')[0])[1:]
            temp_df = pd.read_csv(StringIO(output.split('\n', 1)[1]), delimiter=r"\s{2,}", names=headers)
            temp_df
            if '[' in str(temp_df.index[-1]):
                temp_df.drop(temp_df.tail(1).index, inplace=True)
            output = temp_df.to_html(classes='table', table_id='table'+str(numtables), max_cols=500)
            numtables += 1
        else:
            outputtype = 'string'
        return [outputtype, output, ldict, numtables, numplots]
    # if it was a plot, then output as HTML image from buffer
    else:
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        output = "<img id='image{0}' src='data:image/png;base64,{1}'/>".format(numplots, data)
        outputtype = 'image'
        numplots += 1
        ldict.update(tldict)
        return [outputtype, output, ldict, numtables, numplots]


# log outputs in database and return id of new entry
def log_commands(outputs):
    # unpack outputs into variables
    _, cmd, code, _ = outputs
    feedback = 'none'
    dt = str(datetime.now())
    record = Log(dt, cmd, code, feedback)
    db.session.add(record)
    db.session.commit()
    return record.id


# log results to code edit db and return new id
def log_edit(edit):
    command, edited_code, orig_ref = edit
    # overwrite command in Log table, update edit count
    record = Log.query.filter_by(id=orig_ref).first()
    record.command = command
    record.times_edited += 1
    # record new edit and ref_id in CodeEdit table
    edit_entry = CodeEdit(edited_code, orig_ref)
    db.session.add(edit_entry)
    # commit changes and return id of new entry
    db.session.commit()
    return edit_entry.id


# retrieve entry from log db using id
def get_log(id):
    record = Log.query.filter_by(id=id).first()
    cmd = record.command
    codeblock = record.codeblock
    return cmd, codeblock