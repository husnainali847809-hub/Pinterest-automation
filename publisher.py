import os,re,json,base64,hashlib,argparse,textwrap,html
from datetime import datetime,timezone
from io import BytesIO
import requests
from PIL import Image,ImageDraw,ImageFont

API="https://api.github.com"; PAPI="https://api.pinterest.com/v5"
SITES={
"smarttools":{"repo":"husnainali847809-hub/Smart-Tools-Hub","base":"https://husnainali847809-hub.github.io/Smart-Tools-Hub","name":"SmartTools Hub","board":"Smart Tools Hub | Tips & Tutorials","accent":"#6658e8","topics":["How to calculate percentages step by step","How to use a word counter for clearer writing","A practical guide to converting common units","How to format JSON and make data easier to read","Simple ways to create stronger passwords","How to calculate age accurately","When to use a QR code generator","How a character counter helps with social media limits","A beginner-friendly guide to temperature conversion","How to convert colors between HEX and RGB"]},
"templivox":{"repo":"husnainali847809-hub/TemplivoX","base":"https://husnainali847809-hub.github.io/TemplivoX","name":"TemplivoX","board":"TemplivoX | Printable Planners & Templates","accent":"#315b43","topics":["How to build a realistic weekly study plan","How to use a monthly budget planner","A simple daily planner routine for busy weeks","How to track expenses with a spreadsheet","How to prepare for exams with a revision planner","How to use a habit tracker consistently","What to include in a professional invoice template","How to plan a project with a simple checklist","How to use a meal planner to organize a week","How to choose between PDF, Word and Excel templates"]}}
def reqenv(k):
 v=os.getenv(k,"").strip()
 if not v: raise RuntimeError("Missing Actions secret: "+k)
 return v
def esc(x):return html.escape(str(x or ""),quote=True)
def slugify(x):return re.sub(r"[^a-z0-9]+","-",x.lower()).strip("-")[:65]
def article(site,topic,old):
 model=os.getenv("GEMINI_MODEL","gemini-2.5-flash")
 prompt=f"""Write an original evergreen 650-850 word article for {site['name']}. Topic: {topic}.
Use clear natural English for beginners, practical examples, intro, 4-5 sections, bullets and concise conclusion.
Be accurate. Do not invent statistics, studies, quotes or unsupported features. No medical, legal or financial advice.
No copied text, external links or keyword stuffing. Return ONLY JSON:
{{"title":"45-65 character title","description":"140-160 character meta description","excerpt":"1-2 sentence summary","tags":["tag1","tag2","tag3","tag4"],"sections":[{{"heading":"Heading","paragraphs":["paragraph"],"bullets":["point"]}}],"conclusion":"short conclusion"}}
Avoid repeating recent titles: {json.dumps(old[-40:])}"""
 u=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
 r=requests.post(u,params={"key":reqenv("GEMINI_API_KEY")},json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"responseMimeType":"application/json","temperature":0.7}},timeout=120);r.raise_for_status()
 a=json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
 if not all(a.get(k) for k in ("title","description","excerpt","sections","conclusion")) or len(a["sections"])<3:raise ValueError("Incomplete article from Gemini")
 return a
def graphic(site,a):
 im=Image.new("RGB",(1000,1500),"#111827");d=ImageDraw.Draw(im);ac=site["accent"]
 d.rectangle((0,0,1000,25),fill=ac);d.ellipse((650,-150,1250,450),fill=ac);d.ellipse((-250,1050,400,1650),fill="#263448");d.rounded_rectangle((55,65,945,1435),radius=40,outline="#ffffff55",width=3)
 try:b=ImageFont.truetype("DejaVuSans-Bold.ttf",68);n=ImageFont.truetype("DejaVuSans.ttf",32);s=ImageFont.truetype("DejaVuSans-Bold.ttf",25)
 except OSError:b=n=s=ImageFont.load_default()
 d.text((105,125),site["name"].upper(),font=s,fill="white");d.rounded_rectangle((105,205,330,218),radius=6,fill=ac)
 lines=[];line=""
 for w in a["title"].split():
  t=(line+" "+w).strip()
  if d.textbbox((0,0),t,font=b)[2]>770 and line:lines.append(line);line=w
  else:line=t
 if line:lines.append(line)
 y=300
 for x in lines[:6]:d.text((105,y),x,font=b,fill="white");y+=90
 y+=45
 for x in textwrap.wrap(a["excerpt"],44)[:6]:d.text((108,y),x,font=n,fill="#d5dce5");y+=52
 d.rounded_rectangle((105,1135,895,1255),radius=20,fill=ac);d.text((145,1175),"READ THE FULL GUIDE",font=s,fill="white")
 d.text((105,1320),site["base"].replace("https://",""),font=s,fill="#c5ced9")
 out=BytesIO();im.save(out,format="JPEG",quality=91,optimize=True);return out.getvalue()
class GH:
 def __init__(self):
  self.s=requests.Session();self.s.headers.update({"Authorization":"Bearer "+reqenv("GITHUB_CONTENT_TOKEN"),"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"})
 def get(self,repo,path):
  r=self.s.get(f"{API}/repos/{repo}/contents/{path}",params={"ref":"main"},timeout=45)
  if r.status_code==404:return None,None
  r.raise_for_status();j=r.json()
  return (base64.b64decode(j["content"]).decode() if j.get("encoding")=="base64" else None),j["sha"]
 def put(self,repo,path,data,msg,binary=False):
  _,sha=self.get(repo,path);raw=data if binary else data.encode()
  p={"message":msg,"content":base64.b64encode(raw).decode(),"branch":"main"}
  if sha:p["sha"]=sha
  r=self.s.put(f"{API}/repos/{repo}/contents/{path}",json=p,timeout=90);r.raise_for_status()
def render(site,a,slug,date):
 url=f"{site['base']}/blog/{slug}.html";parts=""
 for sec in a["sections"]:
  parts+=f"<section><h2>{esc(sec['heading'])}</h2>"+"".join(f"<p>{esc(p)}</p>" for p in sec.get("paragraphs",[]))
  if sec.get("bullets"):parts+="<ul>"+"".join(f"<li>{esc(x)}</li>" for x in sec["bullets"])+"</ul>"
  parts+="</section>"
 schema=json.dumps({"@context":"https://schema.org","@type":"Article","headline":a["title"],"description":a["description"],"datePublished":date,"mainEntityOfPage":url})
 return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(a['title'])} | {esc(site['name'])}</title><meta name="description" content="{esc(a['description'])}"><meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{url}"><meta property="og:type" content="article"><meta property="og:site_name" content="{esc(site['name'])}"><meta property="og:title" content="{esc(a['title'])}"><meta property="og:description" content="{esc(a['description'])}"><meta property="og:url" content="{url}"><meta property="og:image" content="{site['base']}/assets/pinterest/{slug}.jpg"><meta name="twitter:card" content="summary_large_image"><script type="application/ld+json">{schema}</script><style>*{{box-sizing:border-box}}body{{margin:0;background:#f5f6f7;color:#20252b;font:17px/1.8 system-ui,Arial}}header{{background:#17202b;padding:20px 5%}}header a{{color:white;text-decoration:none;font-weight:800;font-size:22px}}main{{max-width:850px;margin:40px auto;padding:0 20px}}article{{background:white;border:1px solid #e5e8ec;border-radius:18px;padding:clamp(22px,5vw,54px)}}h1{{font-size:clamp(32px,5vw,48px);line-height:1.15}}h2{{font-size:25px;margin-top:34px}}.intro{{font-size:19px;color:#5d6873}}.cta{{background:{site['accent']};color:white;padding:22px;border-radius:14px;margin-top:35px}}.cta a{{background:white;color:{site['accent']};padding:9px 14px;border-radius:8px;text-decoration:none;font-weight:bold}}footer{{text-align:center;color:#78818a;padding:28px}}</style></head><body><header><a href="{site['base']}/">{esc(site['name'])}</a></header><main><article><h1>{esc(a['title'])}</h1><p class="intro">{esc(a['excerpt'])}</p><p><small>Published {date} · {esc(site['name'])}</small></p>{parts}<h2>Final thoughts</h2><p>{esc(a['conclusion'])}</p><div class="cta"><strong>{esc(site['name'])}</strong><p>Explore more helpful resources on our website.</p><a href="{site['base']}/">Visit website</a></div></article></main><footer>© {datetime.now(timezone.utc).year} {esc(site['name'])}</footer></body></html>"""
def publish_site(gh,site,a,slug,date,img):
 repo=site["repo"];path=f"blog/{slug}.html";gh.put(repo,path,render(site,a,slug,date),"Publish article: "+a["title"])
 imgpath=f"assets/pinterest/{slug}.jpg";gh.put(repo,imgpath,img,"Add Pinterest graphic",True)
 old,_=gh.get(repo,"blog/index.html");matches=re.findall(r"<article>.*?</article>",old or "",re.S)
 card=f'<article><h2><a href="{slug}.html">{esc(a["title"])}</a></h2><p>{esc(a["excerpt"])}</p><a href="{slug}.html">Read article</a></article>'
 cards=card+"".join(x for x in matches if slug not in x)
 idx=f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Blog | {esc(site["name"])}</title></head><body style="font:17px/1.7 system-ui;max-width:850px;margin:40px auto;padding:20px"><h1>{esc(site["name"])} Guides</h1>{cards}</body></html>'
 gh.put(repo,"blog/index.html",idx,"Update blog index")
 sm,_=gh.get(repo,"sitemap.xml")
 if sm:
  for sitemap_url in (f"{site['base']}/blog/",f"{site['base']}/{path}"):
   if sitemap_url not in sm:
    sm=sm.replace("</urlset>",f"<url><loc>{sitemap_url}</loc><lastmod>{date}</lastmod></url></urlset>")
  gh.put(repo,"sitemap.xml",sm,"Update sitemap")
 return f"{site['base']}/{path}",f"https://raw.githubusercontent.com/{repo}/main/{imgpath}"
class Pinterest:
 def __init__(self):
  token=os.getenv("PINTEREST_ACCESS_TOKEN","").strip()
  app_id=os.getenv("PINTEREST_APP_ID","").strip()
  app_secret=os.getenv("PINTEREST_APP_SECRET","").strip()
  refresh=os.getenv("PINTEREST_REFRESH_TOKEN","").strip()
  if app_id and app_secret and refresh:
   rr=requests.post(PAPI+"/oauth/token",auth=(app_id,app_secret),data={"grant_type":"refresh_token","refresh_token":refresh},timeout=45)
   rr.raise_for_status(); token=rr.json()["access_token"]
   if rr.json().get("refresh_token") and rr.json()["refresh_token"]!=refresh:
    print("WARNING: Pinterest rotated the refresh token; update PINTEREST_REFRESH_TOKEN in repository secrets.")
  if not token: raise RuntimeError("Set PINTEREST_ACCESS_TOKEN or all three Pinterest refresh-token secrets.")
  self.s=requests.Session();self.s.headers.update({"Authorization":"Bearer "+token,"Content-Type":"application/json"})
 def board(self,name):
  r=self.s.get(PAPI+"/boards",params={"page_size":100},timeout=45);r.raise_for_status()
  for x in r.json().get("items",[]):
   if x.get("name","").lower()==name.lower():return x["id"]
  r=self.s.post(PAPI+"/boards",json={"name":name,"description":"Useful guides and ideas","privacy":"PUBLIC"},timeout=45);r.raise_for_status();return r.json()["id"]
 def create(self,b,a,url,img):
  tags=" ".join("#"+re.sub(r"[^A-Za-z0-9]","",x.replace(" ","")) for x in a.get("tags",[])[:4])
  p={"board_id":b,"title":a["title"][:100],"description":(a["excerpt"]+" "+tags)[:490],"link":url,"alt_text":"Pinterest guide: "+a["title"],"media_source":{"source_type":"image_url","url":img,"is_standard":True}}
  r=self.s.post(PAPI+"/pins",json=p,timeout=90);r.raise_for_status();return r.json()
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--cron",default=os.getenv("SCHEDULE_CRON",""));ap.add_argument("--site",default=os.getenv("MANUAL_SITE",""));ap.add_argument("--dry-run",action="store_true");args=ap.parse_args()
 schedule={"0 3 * * *":("smarttools","08:00 PKT"),"0 7 * * *":("templivox","12:00 PKT"),"0 11 * * *":("smarttools","16:00 PKT"),"0 15 * * *":("templivox","20:00 PKT")}
 key,slot=(args.site,"manual") if args.site else schedule.get(args.cron,(None,None))
 if key not in SITES:raise ValueError("Choose a valid website or schedule slot")
 site=SITES[key];date=datetime.now(timezone.utc).date().isoformat()
 state=json.load(open("seen.json")) if os.path.exists("seen.json") else {"titles":[],"published_slots":[]}
 slotkey=f"{date}:{slot}:{key}"
 if slotkey in state.get("published_slots",[]):print("Already published for this slot.");return
 topic=site["topics"][(len(state.get("titles",[]))//2)%len(site["topics"])]
 a=article(site,topic,state.get("titles",[]));suffix=hashlib.sha1((date+key+a["title"]).encode()).hexdigest()[:5];slug=f"{date}-{slugify(a['title'])}-{suffix}";img=graphic(site,a)
 if args.dry_run:print("DRY RUN: "+json.dumps({"site":site["name"],"topic":topic,"title":a["title"],"slug":slug},indent=2));return
 gh=GH();url,image_url=publish_site(gh,site,a,slug,date,img);pt=Pinterest();board=pt.board(site["board"]);result=pt.create(board,a,url,image_url)
 state.setdefault("titles",[]).append(a["title"]);state["titles"]=state["titles"][-200:]
 state.setdefault("published_slots",[]).append(slotkey);state["published_slots"]=state["published_slots"][-120:]
 json.dump(state,open("seen.json","w"),ensure_ascii=False,indent=2)
 print("PUBLISHED ARTICLE:",url);print("PINTEREST PIN ID:",result.get("id"))
if __name__=="__main__":main()
