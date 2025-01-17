import json, collections, argparse
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc

parser = argparse.ArgumentParser(description='Fetch history of specified Slack channel.')

parser.add_argument('--input', '-input', default='history.json', help='Input file name with Slack history to anlyse (default: %(default)s).')
parser.add_argument('--title', '-title', default='Number of issues/threads per month', help='Chart title (default: %(default)s).')
parser.add_argument('--xlabel', '-xlabel', default='Month', help='Chart x label (default: %(default)s).')
parser.add_argument('--ylabel', '-ylabel', default='Number of threads', help='Chart y label (default: %(default)s).')
parser.add_argument('--threads', '-threads', default=[], help='Threads config', type=json.loads)

args = parser.parse_args()

input = args.input
title = args.title
xlabel = args.xlabel
ylabel = args.ylabel

def validateThreads(threads):
  for t in threads:
    if not 'debug' in t:
      t['debug'] = False
    if not 'color' in t:
      t['color'] = randomColor()
    if not 'name' in t:
      print('No "name" field in threads configuration')
      quit()
    if not 'keywords' in t:
      print('No "keywords" field in threads configuration')
      quit()
  return threads

def randomColor():
  return np.random.rand(3,)

def drawStackedBarPlot(allThreads, subThreads, title, xlabel, ylabel):
  # y-axis in bold
  rc('font', weight='bold')
 
  # The position of the bars on the x-axis
  r = []
  # Names of x bars
  names = []
  barHeighs = []
  index = 0
  for key, value in allThreads.iteritems():
    r.append(index)
    index += 1
    names.append("%.2f" % key)
    barHeighs.append(0)
  barWidth = 0.65

  for sub in subThreads:
    bar = []
    bottom = []
    for b in barHeighs:
      bottom.append(b)
    index = 0
    for month, value in sub['threadsPerMonth'].iteritems():
      bar.append(value)
      barHeighs[index] += value
      index += 1
    plt.bar(r, bar, bottom=bottom, color=[sub['color']], edgecolor='white', width=barWidth, label=sub['name'])

  bar = []
  index = 0
  for month, value in allThreads.iteritems():
    bar.append(value - barHeighs[index])
    index += 1

  plt.bar(r, bar, bottom=barHeighs, color='#800080', edgecolor='white', width=barWidth, label='Other') 
 
  # Custom X & Y axis
  plt.xticks(r, names, fontweight='bold')
  plt.title(title.decode('utf-8'))
  plt.xlabel(xlabel.decode('utf-8'))
  plt.ylabel(ylabel.decode('utf-8'))
   
  # Show graphic
  plt.legend()
  plt.show()


with open(input) as f:
  messages = json.load(f)

def tsToDate(ts):
  return datetime.fromtimestamp(int(float(ts)))

def prettyTS(ts):
  return tsToDate(ts).strftime("%Y-%m-d")

print('Number of all messages: {}'.format(len(messages)))

def threadsWithKeywordsPerMonth(messages, keywords, debug):
  lastThread = ''
  matchInThread = 0
  threadsPerMonth = {}

  for m in messages:
    date = tsToDate(m['ts'])
    key = date.year % 2000 + date.month/100.0
    counter = threadsPerMonth.get(key, 0)
    # init month with 0 value
    if counter == 0:
      threadsPerMonth[key] = counter
   
    if 'thread_ts' in m and m['ts'] == m['thread_ts'] and m['reply_users_count'] > 0:
      if matchInThread and lastThread != '':
        threadsPerMonth[key] = counter + 1
      lastThread = m['ts']
      matchInThread = False

    if not matchInThread and lastThread != '' and 'text' in m and (('thread_ts' in m and m['ts'] == m['thread_ts'] and m['reply_users_count'] > 0) or ('thread_ts' in m and m['ts'] != m['thread_ts'])):
      text = m['text'].lower().encode('utf-8')
      for w in keywords:
        if w in m['text']:
          matchInThread = True
          if debug:
            print('Found \'{}\' keyword in: {}'.format(w, text))
          break
  return collections.OrderedDict(sorted(threadsPerMonth.items()))

allThreads = threadsWithKeywordsPerMonth(messages, [' '], False)

subThreads = validateThreads(args.threads)
for subThread in subThreads:
  subThread['threadsPerMonth'] = threadsWithKeywordsPerMonth(messages, subThread['keywords'], subThread['debug'])

drawStackedBarPlot(allThreads, subThreads, title, xlabel, ylabel)

