# imports
import os
import sys
import numpy as np
import pandas as pd
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
import time

from .models import db, User, Log

s00 = '''import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import shap
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split'''

codex_context = '# import standard libraries\n' + s00 + '\n'
codex_filename = 'codex_script_' + re.sub('\.[0-9]+', '', str(datetime.now()).replace(' ', '_').replace(':', '_')) + '.txt'
codex_filename = os.path.join('codex_logs', codex_filename)

error_msg = 'Sorry, something went wrong. Please check the code and edit as needed.'

old_stdout = sys.stdout

ldict = {}
exec(s00, ldict)
numtables = 0
numplots = 0


# submit codex API call
def codex_call(prompt):
    start = time.time()
    response = openai.Completion.create(
        model="code-davinci-002",
        prompt=codex_context,
        temperature=0.01,
        max_tokens=4000,
        frequency_penalty=1,
        presence_penalty=1,
        stop=["#", "'''", '"""']
        )
    end = time.time()
    elapsed = end - start
    return response['choices'][0]['text'], elapsed


def runcode(code):
    global numtables, numplots, error_msg
    # turn off plotting and run function, try to grab fig and save in buffer
    tldict = ldict.copy()
    plt.ioff()
    try:
        exec(code, tldict)
    except KeyError:
        pass
    except:
        print(error_msg)
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
            print(error_msg)
        output = new_stdout.getvalue()
        sys.stdout = old_stdout

        # further parsing to determine if plain string or dataframe
        if bool(re.search('Index', output)):
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
        return [outputtype, output]
    # if it was a plot, then output as HTML image from buffer
    else:
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        output = "<img id='image{0}' src='data:image/png;base64,{1}'/>".format(numplots, data)
        outputtype = 'image'
        numplots += 1
        ldict.update(tldict)
        return [outputtype, output]


def log_commands(outputs):
    # unpack outputs into variables
    _, cmd, code, _ = outputs
    feedback = 'none'
    dt = str(datetime.now())
    record = Log(dt, cmd, code, feedback)
    db.session.add(record)
    db.session.commit()
    return record.id


# log results to code edit db
def log_edit(edit):
    dt = str(datetime.now())
    command, orig_code, edited_code, orig_ref = edit
    record = Log.query.filter_by(id=orig_ref).first()
    record.command = command
    record.codeblock = edited_code
    record.times_edited += 1
    db.session.add(record)
    db.session.commit()
    return record.id


# retrieve entry from log db using id
def get_log(id):
    record = Log.query.filter_by(id=id).first()
    cmd = record.command
    codeblock = record.codeblock
    return cmd, codeblock