"""Adds slide transitions and staggered 'rise & fade' entrance animations.
Shapes named aN_* animate in order N (same N = together); title placeholders first."""
import re, sys, zipfile, shutil
src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
zout = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)

def effect(ids, spid, delay, first_in_group, is_text):
    n = lambda: next(ids)
    node = "afterEffect" if first_in_group else "withEffect"
    grp = ' grpId="0"'
    return f'''<p:par><p:cTn id="{n()}" fill="hold"><p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>
<p:par><p:cTn id="{n()}" presetID="42" presetClass="entr" presetSubtype="0" fill="hold"{grp} nodeType="{node}"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
<p:set><p:cBhvr><p:cTn id="{n()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>
<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{n()}" dur="600"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>
<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{n()}" dur="600" decel="100000" fill="hold"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="#ppt_y+0.04"/></p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="#ppt_y"/></p:val></p:tav></p:tavLst></p:anim>
</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>'''

TRANSITIONS = ['<p:fade/>', '<p:push dir="u"/>', '<p:fade/>', '<p:push dir="l"/>']
for item in zin.infolist():
    data = zin.read(item.filename)
    m = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", item.filename)
    if m:
        num = int(m.group(1))
        xml = data.decode("utf8")
        shapes = re.findall(r'<p:(sp|pic)>\s*<p:nv\w+Pr>\s*<p:cNvPr id="(\d+)" name="([^"]*)"', xml)
        groups = {}
        for kind, sid, name in shapes:
            mm = re.match(r"a(\d+)_", name)
            if mm: order = int(mm.group(1))
            elif name.startswith("Text "): order = 0
            else: continue
            groups.setdefault(order, []).append((sid, kind))
        ids = iter(range(3, 100000))
        pars, bld = [], []
        for order in sorted(groups):
            for i, (sid, kind) in enumerate(groups[order]):
                pars.append(effect(ids, sid, 0, i == 0, kind == "sp"))
                if kind == "sp": bld.append(f'<p:bldP spid="{sid}" grpId="0" animBg="1"/>')
        timing = f'''<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>
<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>
<p:par><p:cTn id="{next(ids)}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>
{''.join(pars)}
</p:childTnLst></p:cTn></p:par>
</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>
</p:childTnLst></p:cTn></p:par></p:tnLst><p:bldLst>{''.join(bld)}</p:bldLst></p:timing>'''
        trans = f'<p:transition spd="slow">{TRANSITIONS[(num - 1) % len(TRANSITIONS)]}</p:transition>'
        xml = re.sub(r"<p:transition.*?</p:transition>|<p:timing>.*?</p:timing>", "", xml, flags=re.S)
        xml = xml.replace("</p:clrMapOvr>", "</p:clrMapOvr>" + trans + timing, 1) if "</p:clrMapOvr>" in xml else xml.replace("</p:cSld>", "</p:cSld>" + trans + timing, 1)
        data = xml.encode("utf8")
    zout.writestr(item, data)
zout.close()
print("animated", dst)
