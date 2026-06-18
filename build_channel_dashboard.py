# -*- coding: utf-8 -*-
"""
河野メリクロン｜流通チャネル分析ダッシュボード生成スクリプト
事実データ × フェルミ推計を計算し、外部ライブラリ非依存の単一HTML（自前SVG）を出力する。
全ての図は本スクリプトの計算結果から座標を生成するため、本文・計算ロジック表・グラフが一致する。
"""

# ============================================================
# 0. 配色・基礎データ
# ============================================================
INK="#2c2c2a"; MUTE="#6b6a66"; FAINT="#9a9994"; BORDER="#e4e2d9"; PANEL="#faf9f5"
C_NEWS="#b0563f"   # 新聞通販（縮む・高齢）
C_TV  ="#cf924b"   # TV通販
C_EC  ="#3f8f7d"   # EC（伸びる・現役）
C_GIFT="#9c6bae"   # ギフト
C_STORE="#5b82a8"  # 実店舗
# 年代色（若→老：緑〜赤のグラデーション。直感的に「若い＝緑、古い＝赤」）
AGE_COLORS={'20代':"#5fa899",'30代':"#8cbf83",'40代':"#dcc862",'50代':"#e0a052",'60代':"#cf7350",'70代以上':"#a8443a"}
AGES=['20代','30代','40代','50代','60代','70代以上']

# 年代別人口（万人・総務省2024）
POP={'20代':1260,'30代':1290,'40代':1510,'50代':1720,'60代':1450,'70代以上':2898}

def age_comp(rates):
    """人口×利用率/接触率 → 顧客年代構成比(%)"""
    reach={k:POP[k]*rates[k] for k in POP}; tot=sum(reach.values())
    return {k:reach[k]/tot*100 for k in POP}

# --- 各チャネルの利用率/接触率（確定値＝出典明示、推計＝近接データから補間） ---
RATE_NEWS={'20代':0.10,'30代':0.167,'40代':0.28,'50代':0.438,'60代':0.603,'70代以上':0.749} # 新聞月ぎめ購読率(新聞通信調査会2024)。20/40代は補間(推計)
RATE_TV  ={'20代':0.16,'30代':0.17,'40代':0.31,'50代':0.43,'60代':0.48,'70代以上':0.40}     # TV通販利用経験(コマースピック等)。60/70代は補間(推計)
RATE_EC  ={'20代':0.80,'30代':0.82,'40代':0.75,'50代':0.65,'60代':0.46,'70代以上':0.25}     # ネットショッピング個人利用率(推計)。既知EC客60代以上24.6%に較正
RATE_GIFT={'20代':0.82,'30代':0.75,'40代':0.65,'50代':0.55,'60代':0.22,'70代以上':0.08}     # ソーシャルギフト利用率(ギフトモール2025、15-59歳)。60代以上は外挿(推計)
RATE_DGS ={'20代':0.78,'30代':0.85,'40代':0.88,'50代':0.88,'60代':0.85,'70代以上':0.72}     # DgS購買接触(推計・生活必需で全世代厚い)

COMP={
 '新聞通販':age_comp(RATE_NEWS),
 'TV通販':age_comp(RATE_TV),
 'ドラッグストア':age_comp(RATE_DGS),
 'EC（ネット通販）':age_comp(RATE_EC),
 'eギフト':age_comp(RATE_GIFT),
}

# ============================================================
# 1. SVGヘルパー
# ============================================================
def esc(s): return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def svg_open(w,h,vb=None):
    vb=vb or f"0 0 {w} {h}"
    return f'<svg width="100%" viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif">'

def txt(x,y,s,size=12,fill=INK,anchor='start',weight='400',ls=''):
    l=f' letter-spacing="{ls}"' if ls else ''
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{l}>{esc(s)}</text>'

# ---- 逆クロス：二軸折れ線 ----
def dual_line(news, net, W=820, H=360):
    ml,mr,mt,mb=58,58,38,46; pw=W-ml-mr; ph=H-mt-mb
    x0,x1=2002,2025
    def X(yr): return ml+(yr-x0)/(x1-x0)*pw
    L0,L1=0,1.1     # 新聞広告費 兆円（左軸）
    R0,R1=0,60      # ネット通販利用率 %（右軸）
    def YL(v): return mt+ph-(v-L0)/(L1-L0)*ph
    def YR(v): return mt+ph-(v-R0)/(R1-R0)*ph
    s=[svg_open(W,H)]
    s.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{PANEL}" rx="8"/>')
    # グリッド＋左軸ラベル(兆円)
    for gv in [0,0.25,0.5,0.75,1.0]:
        y=YL(gv); s.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{ml+pw}" y2="{y:.1f}" stroke="{BORDER}" stroke-width="1"/>')
        s.append(txt(ml-8,y+4,f'{gv:.2f}',10,FAINT,'end'))
    # 右軸ラベル(%)
    for gv in [0,20,40,60]:
        y=YR(gv); s.append(txt(ml+pw+8,y+4,f'{gv}%',10,C_EC,'start'))
    # x軸年
    for yr in [2002,2008,2014,2020,2025]:
        s.append(txt(X(yr),H-mb+20,str(yr),10,MUTE,'middle'))
    # 新聞広告費（縮む）
    npts=[(2005,1.0377),(2014,0.6057),(2024,0.3417),(2025,0.3136)]
    d='M '+' L '.join(f'{X(a):.1f} {YL(b):.1f}' for a,b in npts)
    s.append(f'<path d="{d}" fill="none" stroke="{C_NEWS}" stroke-width="3" stroke-linejoin="round"/>')
    for a,b in npts: s.append(f'<circle cx="{X(a):.1f}" cy="{YL(b):.1f}" r="4" fill="{C_NEWS}"/>')
    # ネット通販利用率（伸びる）
    epts=[(2002,5.3),(2012,21.6),(2017,34.3),(2024,55.3)]
    d='M '+' L '.join(f'{X(a):.1f} {YR(b):.1f}' for a,b in epts)
    s.append(f'<path d="{d}" fill="none" stroke="{C_EC}" stroke-width="3" stroke-linejoin="round"/>')
    for a,b in epts: s.append(f'<circle cx="{X(a):.1f}" cy="{YR(b):.1f}" r="4" fill="{C_EC}"/>')
    # 端点の注記
    s.append(txt(X(2005)-2,YL(1.0377)-10,'1.04兆円',11,C_NEWS,'start','700'))
    s.append(txt(X(2025),YL(0.3136)-10,'0.31兆円',11,C_NEWS,'end','700'))
    s.append(txt(X(2002)+2,YR(5.3)-10,'5.3%',11,C_EC,'start','700'))
    s.append(txt(X(2024),YR(55.3)-12,'55.3%',11,C_EC,'end','700'))
    # 凡例
    s.append(f'<rect x="{ml}" y="8" width="14" height="4" fill="{C_NEWS}" rx="2"/>')
    s.append(txt(ml+20,15,'新聞広告費（兆円・左軸）電通',10,C_NEWS,'start','600'))
    s.append(f'<rect x="{ml+300}" y="8" width="14" height="4" fill="{C_EC}" rx="2"/>')
    s.append(txt(ml+320,15,'ネット通販 世帯利用率（％・右軸）総務省',10,C_EC,'start','600'))
    s.append('</svg>')
    return ''.join(s)

# ---- 100%積み上げ横棒（年代構成） ----
def hbar100(rows, W=820, label_w=132, note_w=150):
    rh=34; gap=12; H=len(rows)*(rh+gap)+58
    bar_x=label_w; bar_w=W-label_w-note_w
    s=[svg_open(W,H)]
    # 凡例
    lx=label_w
    for a in AGES:
        s.append(f'<rect x="{lx}" y="6" width="12" height="12" fill="{AGE_COLORS[a]}" rx="2"/>')
        s.append(txt(lx+16,16,a,10,MUTE,'start')); lx+=64
    for i,(name,comp,note,hl) in enumerate(rows):
        y=42+i*(rh+gap)
        s.append(txt(label_w-10,y+rh/2+1,name,12.5,INK,'end','700' if hl else '600'))
        x=bar_x
        for a in AGES:
            w=comp[a]/100*bar_w
            s.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{rh}" fill="{AGE_COLORS[a]}"/>')
            if comp[a]>=7:
                s.append(txt(x+w/2,y+rh/2+4,f'{comp[a]:.0f}',10.5,'#ffffff','middle','700'))
            x+=w
        s.append(f'<rect x="{bar_x}" y="{y}" width="{bar_w}" height="{rh}" fill="none" stroke="{BORDER}"/>')
        s.append(txt(bar_x+bar_w+10,y+rh/2+1,note,10.5,hl or MUTE,'start','700' if hl else '400'))
    s.append('</svg>')
    return ''.join(s)

# ---- 横棒（規模・積み上げ対応） ----
def size_bars(items, W=820, label_w=178, maxv=None, unit='兆円'):
    # items: (name, segments[(val,color,seglabel|None)], sub)
    rh=30; gap=24; H=len(items)*(rh+gap)+18
    bx=label_w; bw=W-label_w-150
    maxv=maxv or max(sum(s[0] for s in segs) for _,segs,_ in items)
    s=[svg_open(W,H)]
    for i,(name,segs,sub) in enumerate(items):
        y=12+i*(rh+gap); tot=sum(v for v,_,_ in segs)
        s.append(txt(label_w-10,y+rh/2+1,name,12,INK,'end','600'))
        s.append(f'<rect x="{bx}" y="{y}" width="{bw}" height="{rh}" fill="#f0efe9" rx="3"/>')
        x=bx
        for v,col,seglab in segs:
            w=v/maxv*bw
            s.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{rh}" fill="{col}"/>')
            if seglab and w>44:
                s.append(txt(x+w/2,y+rh/2+4,seglab,10,'#fff','middle','700'))
            x+=w
        s.append(f'<rect x="{bx}" y="{y}" width="{(tot/maxv*bw):.1f}" height="{rh}" fill="none" stroke="{BORDER}" rx="3"/>')
        s.append(txt(x+8,y+rh/2+1,f'{tot:.2f}{unit}',11.5,INK,'start','700'))
        if sub: s.append(txt(bx,y+rh+13,sub,10,FAINT,'start'))
    s.append('</svg>')
    return ''.join(s)

# ---- 横棒（規模・兆円・単純） ----
def hbars(items, W=820, label_w=150, maxv=None, unit='兆円', fmt='{:.1f}'):
    rh=30; gap=12; H=len(items)*(rh+gap)+24
    bx=label_w; bw=W-label_w-150
    maxv=maxv or max(v for _,v,_,_ in items)
    s=[svg_open(W,H)]
    for i,(name,val,col,sub) in enumerate(items):
        y=14+i*(rh+gap); w=val/maxv*bw
        s.append(txt(label_w-10,y+rh/2+1,name,12,INK,'end','600'))
        s.append(f'<rect x="{bx}" y="{y}" width="{bw}" height="{rh}" fill="#f0efe9" rx="3"/>')
        s.append(f'<rect x="{bx}" y="{y}" width="{w:.1f}" height="{rh}" fill="{col}" rx="3"/>')
        s.append(txt(bx+w+8,y+rh/2+1,fmt.format(val)+unit,11.5,INK,'start','700'))
        if sub: s.append(txt(bx+w+8,y+rh/2+14,sub,9.5,FAINT,'start'))
    s.append('</svg>')
    return ''.join(s)

# ---- 成長時系列（複線・指数なし、対数風に実額） ----
def growth_lines(series, W=820, H=380):
    ml,mr,mt,mb=54,120,30,40; pw=W-ml-mr; ph=H-mt-mb
    yrs=[2004,2014,2024]
    def X(i): return ml+i/(len(yrs)-1)*pw
    vmax=16
    def Y(v): return mt+ph-(v/vmax)*ph
    s=[svg_open(W,H)]
    s.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{PANEL}" rx="8"/>')
    for gv in [0,4,8,12,16]:
        y=Y(gv); s.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{ml+pw}" y2="{y:.1f}" stroke="{BORDER}"/>')
        s.append(txt(ml-8,y+4,f'{gv}',10,FAINT,'end'))
    s.append(txt(ml-8,mt-8,'兆円',9,FAINT,'end'))
    for i,yr in enumerate(yrs):
        s.append(txt(X(i),H-mb+22,f'{yr}年頃',10,MUTE,'middle'))
    for name,vals,col,dash in series:
        d='M '+' L '.join(f'{X(i):.1f} {Y(v):.1f}' for i,v in enumerate(vals))
        da=f' stroke-dasharray="{dash}"' if dash else ''
        s.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.6" stroke-linejoin="round"{da}/>')
        for i,v in enumerate(vals): s.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.5" fill="{col}"/>')
        lv=vals[-1]
        s.append(txt(ml+pw+8,Y(lv)+4,f'{name} {lv:.2f}',10.5,col,'start','700'))
    s.append('</svg>')
    return ''.join(s)

# ---- カテゴリ構成（100%積み上げ横棒＋下部凡例・汎用） ----
def cat_bar(name, segs, W=820, label_w=132, hi=None):
    # segs: list of (label, pct, color)。hi=強調するカテゴリ名（縁取り）
    rh=38; by=8; bx=label_w; bw=W-label_w-20
    s=[]; x=bx
    for lab,pct,col in segs:
        w=pct/100*bw
        stroke=f' stroke="{INK}" stroke-width="2"' if lab==hi else ''
        s.append(f'<rect x="{x:.1f}" y="{by}" width="{w:.1f}" height="{rh}" fill="{col}"{stroke}/>')
        if pct>=10:
            s.append(txt(x+w/2,by+rh/2+4,f'{pct:.0f}%',11,'#fff','middle','700'))
        elif pct>=4:
            s.append(txt(x+w/2,by+rh/2+4,f'{pct:.0f}',10,'#fff','middle','700'))
        x+=w
    s.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{rh}" fill="none" stroke="{BORDER}"/>')
    s.append(txt(label_w-10,by+rh/2+1,name,12.5,INK,'end','700'))
    # 凡例（チップを折り返し配置）
    ly=by+rh+18; lx=bx
    for lab,pct,col in segs:
        chip=f'{lab} {pct:.0f}%'; wch=len(chip)*7.0+22
        if lx+wch>W-10: lx=bx; ly+=20
        s.append(f'<rect x="{lx}" y="{ly-9}" width="11" height="11" rx="2" fill="{col}"/>')
        bold='700' if lab==hi else '400'
        col_t=INK if lab==hi else MUTE
        s.append(txt(lx+15,ly,chip,10.5,col_t,'start',bold))
        lx+=wch
    Htot=ly+14
    return svg_open(W,Htot)+''.join(s)+'</svg>'

# ============================================================
# 2. ページ組み立て
# ============================================================
CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f4f3ee;color:#2c2c2a;line-height:1.7;padding:24px}
.wrap{max-width:920px;margin:0 auto}
.card{background:#fff;border-radius:14px;padding:30px 34px;box-shadow:0 2px 14px rgba(0,0,0,.06);margin-bottom:20px}
.hero{background:linear-gradient(135deg,#fbfaf6,#f1efe7);border:1px solid #e4e2d9}
h1{font-size:23px;font-weight:700;letter-spacing:.02em;margin-bottom:8px}
h2{font-size:18px;font-weight:700;margin-bottom:4px;display:flex;align-items:center;gap:10px}
h2 .no{display:inline-flex;width:28px;height:28px;border-radius:8px;background:#2c2c2a;color:#fff;font-size:14px;align-items:center;justify-content:center;flex:none}
.lead{font-size:13.5px;color:#6b6a66;margin-bottom:18px}
.sub{font-size:13px;color:#888;margin-bottom:4px}
p{font-size:13.5px;margin-bottom:12px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0}
.kpi{background:#faf9f5;border:1px solid #e4e2d9;border-radius:10px;padding:14px 12px}
.kpi .v{font-size:22px;font-weight:700;line-height:1.2}
.kpi .l{font-size:11px;color:#6b6a66;margin-top:4px}
.tag{display:inline-block;font-size:10.5px;font-weight:700;padding:2px 9px;border-radius:20px;margin-right:6px}
.t-fact{background:#e7f0ec;color:#2f6b58}
.t-fermi{background:#f3e9d6;color:#9a6b1e}
.note{font-size:11.5px;color:#9a9994;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:12px;margin:10px 0}
th,td{border:1px solid #e4e2d9;padding:7px 9px;text-align:left;vertical-align:top}
th{background:#faf9f5;font-weight:700;color:#4a4945}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.legend-note{font-size:11.5px;color:#6b6a66;background:#faf9f5;border-left:3px solid #cf924b;padding:8px 12px;border-radius:0 6px 6px 0;margin:10px 0}
.concl{background:#fbf4f1;border:1px solid #ecd9d1;border-radius:10px;padding:16px 18px;margin:12px 0}
.concl h3{font-size:14.5px;color:#b0563f;margin-bottom:6px}
.flag{background:#fff8e6;border:1px solid #f0e2b8;border-radius:8px;padding:10px 14px;font-size:12px;color:#7a5d12;margin:10px 0}
.src{font-size:11.5px;color:#6b6a66;line-height:1.9}
.src b{color:#4a4945}
.chip{font-size:11px;color:#6b6a66;background:#f0efe9;border-radius:6px;padding:3px 8px;margin:2px;display:inline-block}
ul{margin:6px 0 12px 20px;font-size:13px}
li{margin-bottom:5px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:680px){.kpis{grid-template-columns:repeat(2,1fr)}.two{grid-template-columns:1fr}body{padding:12px}.card{padding:20px}}
"""

def tag(kind):
    return '<span class="tag t-fact">確定値</span>' if kind=='fact' else '<span class="tag t-fermi">推計値</span>'

H=[]
H.append('<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">')
H.append('<meta name="viewport" content="width=device-width,initial-scale=1.0">')
H.append('<title>河野メリクロン｜流通チャネル分析ダッシュボード</title>')
H.append(f'<style>{CSS}</style></head><body><div class="wrap">')

# ---------- HERO ----------
H.append('<div class="card hero">')
H.append('<h1>流通チャネル分析ダッシュボード</h1>')
H.append('<div class="sub">河野メリクロン（徳島・洋蘭メーカー／育毛剤「蘭夢」）｜通販偏重は時代遅れか？　規模・顧客年代・商品構成と10年/20年の推移で検証</div>')
H.append('<p>結論を先に：<b>新聞という器が半分に縮み、その購読者の約7割が60代以上</b>に偏る一方、<b>ネット通販・ギフト・実店舗は現役世代を取り込んで拡大</b>している。'
         '通販ダイレクト（特に新聞広告経由）は「縮む・高齢・狭い母集団」に閉じており、成長チャネルへの拡張余地が大きい。'
         '以下、すべての数値は<b>出典付きの事実</b>と<b>計算過程を全開示したフェルミ推計</b>で構成する。</p>')
H.append('<div class="kpis">')
for v,l,c in [('▲半減','新聞発行部数 2000→2024年',C_NEWS),('66.7%','新聞通販客の60代以上比率',C_NEWS),
              ('55.3%','ネット通販 世帯利用率2024',C_EC),('×60','eギフト市場 10年伸び',C_GIFT)]:
    H.append(f'<div class="kpi"><div class="v" style="color:{c}">{v}</div><div class="l">{l}</div></div>')
H.append('</div>')
H.append('<p class="note">凡例：<span class="tag t-fact">確定値</span>＝公的統計・IR等の実測／<span class="tag t-fermi">推計値</span>＝近接データからの補間・代表企業の積み上げ。'
         '規模は切り口（受注形態・業態・購買目的）が異なるため<b>足し合わせない</b>。共通の分母は小売総額167兆円（商業動態2024）。</p>')
H.append('</div>')

# ---------- ① 逆クロス ----------
H.append('<div class="card"><h2><span class="no">1</span>逆クロス：新聞の凋落 × ネット通販の台頭</h2>')
H.append('<div class="lead">同じ20年で、片方は半分に縮み、片方は10倍に伸びた。器（媒体）の勢いが正反対であることが、通販偏重リスクの起点。</div>')
H.append(dual_line(None,None))
H.append('<div class="legend-note">'+tag('fact')+
         '　新聞広告費：2005年 <b>1兆377億円</b> → 2024年 <b>3,417億円</b> → 2025年 3,136億円（電通「日本の広告費」、約20年で約7割減）。'
         '新聞発行部数：2000年 5,370万部 → 2024年 2,709万部（日本新聞協会、ほぼ半減）。'
         'ネット通販 世帯利用率：2002年 5.3% → 2024年 <b>55.3%</b>（総務省 家計消費状況調査）。'
         '<span class="note">※2008/2012/2017年の中間点を結んだ折れ線。新聞広告費の媒体内「通販・ダイレクト系」比率は非開示のため、新聞広告費そのものを器の代理指標とした。</span></div>')
H.append('</div>')

# ---------- ② チャネル別 規模 ----------
H.append('<div class="card"><h2><span class="no">2</span>チャネル別の市場規模（切り口が違うので足さない）</h2>')
H.append('<div class="lead">分母は小売総額 167兆円。下記は「受注形態（通販・EC）」「購買目的（ギフト）」「業態（DgS・百貨店）」というレイヤーの違う数字で、重複するため合計しない。'
         '<b>注意：通販総額はECを含む</b>ので、純粋な「昔ながらの通販（新聞/TV/カタログ）＝非EC」を分けて示す。</div>')
sizes=[
 ('通販ダイレクト',[(1.84,C_NEWS,'非EC 1.8'),(13.59,'#cdbfae','EC経由 13.6')],'富士経済2022・物販15.4兆。純粋な非EC通販（新聞/TV/カタログ）は約1.8兆だけ＝総額の12%'),
 ('物販EC',[(15.20,C_EC,None)],'経産省2024・EC化率9.78%（メーカー直販EC等も含む経済全体）'),
 ('ギフト',[(11.19,C_GIFT,None)],'矢野経済2024・10年でほぼ横ばい（+16%）'),
 ('ドラッグストア',[(10.03,C_STORE,None)],'JACDS2024年度・初の10兆円突破'),
 ('百貨店',[(5.77,'#8a6f9c',None)],'協会2024・1991年ピーク9.71兆の約6割'),
]
H.append(size_bars(sizes,maxv=15.43))
H.append('<div class="legend-note">'+tag('fact')+
         '　ここが肝：「通販14.55兆・26年連続増（JADMA）」という見出しは派手だが、<b>その伸びはほぼEC化によるもの</b>。'
         '富士経済2022では通販総額15.4兆のうちEC経由が13.6兆（88%）、<b>新聞・TV・カタログなど非EC通販は約1.8兆円（12%）にすぎない</b>。'
         '小売総額167兆に対し、非EC通販はわずか1.1%。河野メリクロンが偏重するのは、この「縮む1.8兆円の器」の方である。</div>')
H.append('</div>')

# ---------- ③ チャネル別 顧客年代構成（主役の図） ----------
H.append('<div class="card"><h2><span class="no">3</span>チャネル別の顧客年代構成 ＝ 通販は「高齢に閉じる」</h2>')
H.append('<div class="lead">計算式：<b>年代別人口（総務省2024）× 年代別の利用率/接触率 ＝ 顧客の年代構成比</b>。'
         '緑（若年）→赤（高齢）。上にいくほど高齢、下にいくほど若い。</div>')
rows=[
 ('新聞通販',COMP['新聞通販'],'60代↑ 66.7%',C_NEWS),
 ('TV通販',COMP['TV通販'],'50代↑ 74.5%',C_TV),
 ('ドラッグストア',COMP['ドラッグストア'],'60代↑ 40.3%',C_STORE),
 ('EC（ネット通販）',COMP['EC（ネット通販）'],'20-40代 56%',C_EC),
 ('eギフト',COMP['eギフト'],'20-30代 44.7%',C_GIFT),
]
H.append(hbar100(rows))
H.append('<div class="legend-note">'+tag('fermi')+
         '　新聞通販＝新聞月ぎめ購読率（30代16.7%/50代43.8%/60代60.3%/70代以上74.9%・新聞通信調査会2024、20/40代は補間）を接触率に採用。'
         'EC＝既知の「EC客の60代以上24.6%」に較正。eギフト＝ソーシャルギフト利用率（20代女性84.1%・ギフトモール2025）。'
         '<b>新聞通販とeギフトは年代構成がほぼ鏡像</b>＝同じ商品でも届く相手が真逆になる。</div>')
H.append('</div>')

# ---------- ④ 通販 媒体別フェルミ ----------
H.append('<div class="card"><h2><span class="no">4</span>通販ダイレクトの媒体別フェルミ（積み上げ）</h2>')
H.append('<div class="lead">新聞・ラジオ通販は単独の市場統計が非公開（富士経済では「その他」に統合）。'
         'そこで代表企業のIR・業界紙売上を積み上げて規模感を推計する。</div>')
media=[
 ('TV通販 上位4社',0.594,C_TV,'ジャパネット2,908+ショップCh1,678+QVC1,235+テレ東118億'),
 ('カタログ通販',1.13,C_TV,'富士経済2022・縮小傾向（ベルーナ/スクロール/dinos/千趣会等）'),
 ('健食・化粧品通販 主要7社',0.298,C_NEWS,'新聞TV広告主力：再春館/やずや/世田谷/えがお/DHC健食/ファンケル通販/サントリーW国内の一部'),
]
H.append(hbars(media,maxv=1.3,fmt='{:.2f}'))
H.append('<table><tr><th>土台の事実（出典）</th><th>×係数（根拠/仮定）</th><th>＝推計</th><th>区分</th></tr>')
fermi_rows=[
 ('TV通販上位4社 売上 計5,939億円（各社IR/官報2024-25）','÷ 富士経済TV通販6,134億円(2022)','上位4社で市場の約97%を説明','確定×照合'),
 ('健食・化粧品通販7社 計 約9,260億円（業界紙/IR）','× 新聞・TV広告依存度 高（定性）','新聞広告経由ダイレクトの中核プレイヤー群','推計'),
 ('新聞広告費 3,417億円(2024)→3,136億円(2025)','× 通販系比率（非開示・不明）','新聞通販の器は縮小が加速','確定（器）'),
 ('JADMA通販総額 14.55兆円(2024年度)','− EC・カタログ・TV分を除く','新聞・折込・DM等＝残差（個別額は非開示）','推計'),
]
for a,b,c,d in fermi_rows:
    H.append(f'<tr><td>{esc(a)}</td><td>{esc(b)}</td><td><b>{esc(c)}</b></td><td>{esc(d)}</td></tr>')
H.append('</table>')
H.append('<div class="note">感度チェック：健食7社の新聞広告依存度を仮に5割と置いても、新聞経由ダイレクトは約4,600億円規模で「縮む新聞広告費3,100億円」と同オーダー。'
         '係数を上下させても「新聞通販＝小さく縮む器」という結論は揺るがない（頑健）。一方TV通販は微増で、通販内では相対的に底堅い。</div>')
H.append('</div>')

# ---------- ⑤ チャネル別 商品カテゴリ構成 ----------
H.append('<div class="card"><h2><span class="no">5</span>チャネル別の商品カテゴリ構成</h2>')
H.append('<div class="lead">河野メリクロンの主力は「化粧品・育毛剤・健康食品」。各チャネルでこの領域がどれだけ売れているかが拡張余地の目安。'
         '比較のため、メリクロンが現にいる<b>通販ダイレクト</b>の商材構成も先頭に置く。</div>')
H.append(cat_bar('通販ダイレクト（新聞・TV型 単品通販）',[('健康食品・サプリ',40,'#cf924b'),('化粧品・医薬部外品',26,C_NEWS),('衣料・服飾',16,'#8a8f9c'),('食品',10,'#7fae6e'),('雑貨・その他',8,'#bdb9ac')],hi='化粧品・医薬部外品'))
H.append(cat_bar('物販EC（15.2兆円）',[('食品',20.5,'#7fae6e'),('衣類・服飾',18.4,'#c7975a'),('生活家電',18.0,'#5b82a8'),('生活雑貨・家具',16.8,'#9c8bae'),('化粧品・医薬品',7.6,C_EC),('その他',18.7,'#bdb9ac')],hi='化粧品・医薬品'))
H.append(cat_bar('ドラッグストア（10.0兆円）',[('調剤・ヘルスケア',33.2,'#5b82a8'),('フーズ（食品）',28.2,'#7fae6e'),('ホームケア',20.3,'#bdb9ac'),('ビューティケア（化粧品）',18.2,C_STORE)],hi='ビューティケア（化粧品）'))
H.append(cat_bar('百貨店（5.77兆円）',[('衣料・服飾雑貨',38.0,'#c7975a'),('雑貨・家庭用品',20.0,'#9c8bae'),('食料品',26.0,'#7fae6e'),('化粧品',8.1,'#8a6f9c'),('その他',7.9,'#bdb9ac')],hi='化粧品'))
H.append('<div class="legend-note">'+tag('fermi')+
         '　通販ダイレクト：新聞・TV型の単品通販（再春館/やずや/サントリーW/DHC/ファンケル/世田谷等）の商材から推計。健康食品＋化粧品で約66%＝メリクロンの育毛剤・蘭エキス化粧品とほぼ同じ土俵。'
         'なおカタログ通販（ベルーナ/千趣会）は衣料比率が高い別構造。　'+tag('fact')+
         '　EC：経産省2024（食品3.12/衣類2.80/家電2.74/生活雑貨2.56兆円、化粧品・医薬品 約1.15兆円・EC化率8.6〜8.8%）。'
         'DgS：JACDS2024年度（ビューティケア1兆8,272億円＝18.2%）。百貨店：協会2023（化粧品4,416億円＝8.1%）。'
         '<span class="note">EC内訳%は主要4カテゴリ実額を15.2兆で按分（残差その他）。百貨店の衣料・食料は概況からの推計。</span></div>')
H.append('<p style="margin-top:12px"><b>含意：</b>メリクロンが強い「育毛・スキンケア・健食」は、いまの通販ダイレクトでも主力商材だが、'
         '同じ商材がECで約1.15兆円・DgSビューティケアで約1.8兆円という、桁違いに大きく伸びる売り場にも存在する。'
         '化粧品ECは楽天27.8%＋Amazon19.2%＝約47%が主戦場。<b>商材を変えずに、より大きく若い棚へ載せ替えられる</b>のがポイント。</p>')
H.append('</div>')

# ---------- ⑥ 時系列推移（規模） ----------
H.append('<div class="card"><h2><span class="no">6</span>20年の時系列：伸びた器・縮んだ器</h2>')
H.append('<div class="lead">2004年頃 → 2014年頃 → 2024年頃。線が右肩上がりなら成長チャネル、寝ていれば停滞。</div>')
series=[
 ('物販EC',[3.50,6.80,15.20],C_EC,''),
 ('非EC通販',[2.80,2.20,1.84],C_NEWS,'4 3'),
 ('ギフト',[9.50,9.95,11.19],C_GIFT,''),
 ('DgS',[3.80,6.13,10.03],C_STORE,''),
 ('百貨店',[7.80,6.21,5.77],'#8a6f9c','2 3'),
]
H.append(growth_lines(series))
H.append('<div class="legend-note">'+tag('fact')+'＋'+tag('fermi')+
         '　<b>あえて「通販総額（EC込み14.55兆・26年連続増）」ではなく、純粋な非EC通販を載せた。</b>'
         '物販EC：2014年 約6.8兆→2024年 15.2兆（経産省／2004年頃は黎明期で約3.5兆・推計）。'
         '非EC通販（新聞/TV/カタログ）：約2.8兆→2.2兆→1.8兆と<b>漸減</b>（富士経済2022の非EC1.84兆を起点に、カタログ縮小から過去を推計）。'
         'ギフト：9.95兆→11.19兆（+16%）。DgS：5.23兆(2008)→10.03兆。百貨店：1991年ピーク9.71兆→5.77兆。'
         '<span class="note">非EC通販の2004/2014年値は概算（カタログ全盛期から漸減と仮定）。値を上下させても「EC急伸×非EC漸減」の方向は揺るがない。</span></div>')
# eギフトの別枠
H.append('<div class="two" style="margin-top:14px">')
H.append('<div style="background:#faf6fb;border:1px solid #ecdcf0;border-radius:10px;padding:14px 16px">'
         '<div style="font-size:12px;color:#9c6bae;font-weight:700;margin-bottom:6px">eギフト（ソーシャルギフト）の爆発的成長</div>'
         '<div style="font-size:13px;color:#4a4945">2014年度 約82億円 → 2018年度 1,167億円 → 2024年 <b>5,050億円</b> → 2025年予測 6,450億円。'
         '<b>10年で約60倍</b>・年率+20〜28%。ギフティ（4449）売上95.5億円・会員232万人。'
         '<span class="note">※ブリーフ記載の「2,787→4,057億円」は裏取りできず、より新しい矢野経済2026年2月発表値を採用。</span></div></div>')
H.append('<div style="background:#fbf4f1;border:1px solid #ecd9d1;border-radius:10px;padding:14px 16px">'
         '<div style="font-size:12px;color:#b0563f;font-weight:700;margin-bottom:6px">新聞という器の縮小</div>'
         '<div style="font-size:13px;color:#4a4945">発行部数 5,370万部(2000)→2,709万部(2024)で半減。新聞広告費は20年で約7割減。'
         '購読率は70代以上74.9%／30代16.7%と高齢に偏在。非EC通販という器自体が約1.8兆円で漸減。'
         '<b>新規顧客の入口として母集団が縮小・高齢化し続けている。</b></div></div>')
H.append('</div></div>')

# ---------- ⑦ 結論 ----------
H.append('<div class="card"><h2><span class="no">7</span>結論：通販偏重（特に新聞）の時代遅れさ</h2>')
concls=[
 ('① 母集団が「縮む・高齢・狭い」の三重苦','新聞は20年で部数半減・広告費7割減。その読者の購読率は70代以上74.9%に対し30代16.7%。'
  '新聞通販の顧客は計算上60代以上が66.7%（70代以上47.6%）。新規客の入口が構造的に細り、かつ高齢化していく。'),
 ('② 同じ商品でも「届く相手」が真逆','新聞通販（60代以上66.7%）とeギフト（20〜30代44.7%）は年代構成がほぼ鏡像。'
  'EC利用は世帯の55.3%に普及し、客層は20〜40代が56%。通販一本足は、人口が多く購買力のある現役世代をほぼ取りこぼす。'),
 ('③ 伸びる器が複数ある','物販EC15.2兆（10年で2.2倍）、DgS10兆（初突破）、eギフト60倍。'
  '化粧品・育毛・健食はECで約1.15兆・DgSビューティケアで約1.8兆の売り場がある。蘭夢の強みを載せる棚は確かに存在する。'),
 ('④ ただし「通販を捨てる」話ではない','TV通販は微増で底堅く、ファンケル・オルビス等は通販を軸にECへ自然移行して伸びている（オルビスはEC化率5〜6割）。'
  '正しくは「新聞偏重 → 自社EC＋モール＋ギフト＋実店舗への多チャネル化」。既存の高齢優良顧客（リピート資産）は維持しつつ、入口を増やす。'),
]
for t,b in concls:
    H.append(f'<div class="concl"><h3>{esc(t)}</h3><p style="margin:0;font-size:13px">{esc(b)}</p></div>')
H.append('<div class="flag"><b>河野メリクロンの位置づけ：</b>'
         '徳島・美馬市、創業1965年。洋蘭メリクロン苗で世界トップクラス。美容主力は<b>薬用育毛剤「蘭夢（らんむ）」</b>（2003年発売・シンビジウムエキス）。'
         '販路は<b>通販中心</b>（公式ranmu.jp・楽天・Amazon）＋実店舗「あんみつ館」。売上は河野メリクロン販売で約62億円（2019/9期・法人DB値）。'
         '<br>※ブリーフ記載の「蘭エキス化粧品 ミリオラ/Miriora」は複数の一次・二次ソースで確認できず（実在未確認）。確認できた美容ブランドは「蘭夢」。本資料は検証済みの蘭夢を主に記述。</div>')
H.append('<p><b>裏取りの強さ（結論の節度）：</b>「新聞＝縮む・高齢」は新聞協会・新聞通信調査会・電通の複数一次データで裏付く<b>強い結論</b>。'
         '「EC/ギフトが伸びる」は経産省・矢野経済で裏付く<b>強い結論</b>。'
         '一方、各社の新聞広告依存度や媒体別通販額は非開示が多く、媒体別フェルミは<b>「示唆」</b>に留める（係数感度は④節で確認、方向性は頑健）。</p>')
H.append('</div>')

# ---------- ⑧ 計算ロジック表 ----------
H.append('<div class="card"><h2><span class="no">8</span>計算ロジックの全開示（再現可能）</h2>')
H.append('<div class="lead">顧客年代構成は「人口（万人）× 利用率/接触率」で算出。下表の係数を入れ替えれば誰でも再計算できる。</div>')
H.append('<table><tr><th>年代</th><th>人口(万人)</th>'
        +''.join(f'<th>{c}<br><span style="font-weight:400;color:#9a9994">利用率→構成%</span></th>' for c in ['新聞通販','TV通販','EC','eギフト','DgS'])+'</tr>')
rate_map=[('新聞通販',RATE_NEWS,COMP['新聞通販']),('TV通販',RATE_TV,COMP['TV通販']),
          ('EC',RATE_EC,COMP['EC（ネット通販）']),('eギフト',RATE_GIFT,COMP['eギフト']),
          ('DgS',RATE_DGS,COMP['ドラッグストア'])]
for a in AGES:
    H.append(f'<tr><td><b>{a}</b></td><td class="num">{POP[a]:,}</td>')
    for _,rt,cp in rate_map:
        H.append(f'<td class="num">{rt[a]*100:.0f}% → {cp[a]:.1f}%</td>')
    H.append('</tr>')
# 合計行
H.append('<tr style="background:#faf9f5"><td><b>計</b></td><td class="num"><b>{:,}</b></td>'.format(sum(POP.values())))
for nm,rt,cp in rate_map:
    sixty=cp['60代']+cp['70代以上']
    H.append(f'<td class="num"><b>60+ {sixty:.0f}%</b></td>')
H.append('</tr></table>')
H.append('<div class="note">確定値（出典）＝新聞月ぎめ購読率30/50/60/70代（新聞通信調査会2024）、TV通販利用経験20-50代（コマースピック）、ソーシャルギフト利用率（ギフトモール2025）。'
         '推計＝補間値（新聞20/40代、TV60/70代）およびEC各代（既知のEC客60代以上24.6%に較正）・DgS各代（生活必需で全世代厚いと仮定）。'
         '利用率は「接触/利用の有無」であり購入金額構成とは厳密には異なるが、客数ベースの年代偏在を示す指標として用いる。</div>')
H.append('</div>')

# ---------- ⑨ 出典一覧 ----------
H.append('<div class="card"><h2><span class="no">9</span>出典一覧（一次情報優先）</h2>')
srcs=[
 ('市場規模・分母','商業動態統計2024（小売総額167兆円）／経産省「電子商取引に関する市場調査」2024（物販EC15.2兆・EC化率9.78%・カテゴリ別）／JADMA通販市場売上高調査（2004年度3.49兆・2014年度6.15兆・2024年度14.55兆）／富士経済「通販・eコマースビジネスの実態と今後」（カタログ・TV媒体別）'),
 ('新聞・広告','日本新聞協会（発行部数 2000年5,370万→2024年2,709万部）／新聞通信調査会2024（年代別月ぎめ購読率）／電通「日本の広告費」（新聞広告費 2005年1兆377億→2024年3,417億→2025年3,136億）'),
 ('人口・利用率','総務省 人口推計2024（年代別人口）／総務省 家計消費状況調査（ネット通販世帯利用率 2002年5.3%→2024年55.3%）／総務省 通信利用動向調査（個人利用率2023年65.7%）'),
 ('ギフト・EC企業','矢野経済 ギフト市場（2024年11.19兆）・eギフト市場（2024年5,050億→2025年6,450億予測）／ギフトモール2025ソーシャルギフト調査（20代女性84.1%）／ギフティ4449 IR（売上95.5億・会員232万）／プラネット調査（化粧品EC：楽天27.8%・Amazon19.2%・自社16.8%）'),
 ('通販企業IR/業界紙','ジャパネット2,908億・ジュピターショップチャンネル1,678億・QVC1,234億・テレ東ダイレクト118億／ベルーナ2,109億・スクロール840億・dinos476億・千趣会397億・ニッセン約250億／サントリーウエルネス国内1,103億・DHC全社987億(健食529億)・ファンケル通販571億・世田谷自然食品335億・再春館228億・やずや170億・えがお150億／オルビス502億・北の達人112億・プレミアアンチエイジング161億'),
 ('実店舗','JACDS日本のドラッグストア実態調査（2024年度10.03兆・店舗23,723・構成比）／日本百貨店協会（2024年5.77兆・化粧品8.1%・70社178店）／矢野経済 エステティックサロン（2024年3,043億・5年連続減）・理美容向け業務用化粧品（2024年1,611億）／ロフト1,216億・ハンズ605億・フランフラン約400億 等'),
 ('河野メリクロン','公式サイト kawano-mericlone.com／Wikipedia／徳島新聞／@cosme（蘭夢）／Yahoo!しごとカタログ（河野メリクロン販売 約62億・2019/9期）／公式通販 ranmu.jp'),
]
for h,b in srcs:
    H.append(f'<p style="margin-bottom:8px"><b style="color:#4a4945">{esc(h)}</b><br><span class="src">{esc(b)}</span></p>')
H.append('<div class="note">調査上の制約：本分析の数値は一次情報（公的統計・IR・業界紙）に基づくが、収集時に各PDF原本への直接アクセスが制限されたため、'
         '一部は一次情報を引用した報道・検索スニペットでクロス確認した。確定値とした項目は複数ソースで一致を確認済み。'
         '非開示・未確認の項目（媒体別通販額、各社の媒体別チャネル比率、ギフティGMV、百貨店2004/2014年確定額等）は本文中で「非開示／推計／不明」と明記した。'
         '作成日2026年6月16日。</div>')
H.append('</div>')

H.append('<div style="text-align:center;color:#9a9994;font-size:11px;padding:12px">河野メリクロン 流通チャネル分析｜事実とフェルミ推計の透明化ダッシュボード</div>')
H.append('</div></body></html>')

out='/home/user/notion-map/kono-mericlone-channel-analysis.html'
open(out,'w',encoding='utf-8').write(''.join(H))
print('WROTE',out,len(''.join(H)),'bytes')
