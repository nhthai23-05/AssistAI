import React, { useRef, useLayoutEffect } from 'react';
import I from './icons';
import { ActionCard } from './ActionCard';

function renderInline(text) {
  const tokens = [];
  let i = 0;
  while (i < text.length) {
    if (text[i] === "`") {
      const end = text.indexOf("`", i + 1);
      if (end > i) { tokens.push({ t: "code", v: text.slice(i + 1, end) }); i = end + 1; continue; }
    }
    if (text[i] === "*" && text[i + 1] === "*") { tokens.push({ t: "bold-mark" }); i += 2; continue; }
    let j = i;
    while (j < text.length && text[j] !== "`" && !(text[j] === "*" && text[j + 1] === "*")) j++;
    tokens.push({ t: "text", v: text.slice(i, j) });
    i = j;
  }
  const markIdx = tokens.reduce((acc, t, idx) => (t.t === "bold-mark" ? [...acc, idx] : acc), []);
  const paired = new Set();
  for (let k = 0; k + 1 < markIdx.length; k += 2) { paired.add(markIdx[k]); paired.add(markIdx[k + 1]); }

  const out = [];
  let bold = false;
  let bucket = out;
  const stack = [out];
  tokens.forEach((tok, idx) => {
    if (tok.t === "bold-mark") {
      if (paired.has(idx)) {
        if (!bold) { const node = { t: "strong", children: [] }; bucket.push(node); stack.push(node.children); bucket = node.children; bold = true; }
        else { stack.pop(); bucket = stack[stack.length - 1]; bold = false; }
      } else { bucket.push({ t: "text", v: "**" }); }
    } else { bucket.push(tok); }
  });

  const renderNodes = (nodes, prefix = "") =>
    nodes.map((n, ni) => {
      const k = `${prefix}${ni}`;
      if (n.t === "text")   return <React.Fragment key={k}>{n.v}</React.Fragment>;
      if (n.t === "code")   return <code key={k}>{n.v}</code>;
      if (n.t === "strong") return <strong key={k}>{renderNodes(n.children, k + "-")}</strong>;
      return null;
    });
  return renderNodes(out);
}

function renderBody(text) {
  const blocks = text.split(/\n\n+/);
  return blocks.map((block, bi) => {
    const lines = block.split("\n");
    const isOrdered   = lines.every(l => /^\d+\.\s/.test(l));
    const isUnordered = lines.every(l => /^[-•]\s/.test(l));
    if (isOrdered)   return <ol key={bi}>{lines.map((l, li) => <li key={li}>{renderInline(l.replace(/^\d+\.\s/, ""))}</li>)}</ol>;
    if (isUnordered) return <ul key={bi}>{lines.map((l, li) => <li key={li}>{renderInline(l.replace(/^[-•]\s/, ""))}</li>)}</ul>;
    return (
      <p key={bi}>
        {lines.map((l, li) => (
          <React.Fragment key={li}>
            {renderInline(l)}
            {li < lines.length - 1 && <br/>}
          </React.Fragment>
        ))}
      </p>
    );
  });
}

function highlightCode(code) {
  const keywords = ["const","let","var","function","return","if","else","for","while","import","from","export","default","new","await","async","useState","useEffect","SELECT","FROM","WHERE","JOIN","LEFT","ON","GROUP","BY","ORDER","LIMIT","COUNT","AS","INTERVAL","NOW","CREATE","INDEX","TABLE"];
  return code.split("\n").map((line, idx) => {
    const commentMatch = line.match(/^(\s*)(\/\/.*|--.*)/);
    if (commentMatch) return <div key={idx}><span>{commentMatch[1]}</span><span className="com">{commentMatch[2]}</span></div>;
    const tokens = [];
    const pattern = /("[^"\n]*"|'[^'\n]*')|(\b[A-Za-z_$][A-Za-z0-9_$]*\b)|([^\sA-Za-z_$"']+)|(\s+)/g;
    let m;
    while ((m = pattern.exec(line)) !== null) {
      if (m[1]) tokens.push({ t: "str", v: m[1] });
      else if (m[2]) {
        if (keywords.includes(m[2])) tokens.push({ t: "kw", v: m[2] });
        else if (m[2].match(/^[a-z][A-Za-z0-9_$]*$/) && line.slice(pattern.lastIndex, pattern.lastIndex + 1) === "(") tokens.push({ t: "fn", v: m[2] });
        else tokens.push({ t: "id", v: m[2] });
      } else tokens.push({ t: "p", v: m[3] || m[4] });
    }
    return (
      <div key={idx}>
        {tokens.map((tok, ti) => {
          if (tok.t === "kw")  return <span key={ti} className="kw">{tok.v}</span>;
          if (tok.t === "str") return <span key={ti} className="str">{tok.v}</span>;
          if (tok.t === "fn")  return <span key={ti} className="fn">{tok.v}</span>;
          return <span key={ti}>{tok.v}</span>;
        })}
      </div>
    );
  });
}

function Message({ msg, streaming, onActionAccept, onActionReject, msgIdx }) {
  const isUser = msg.role === "user";
  return (
    <div className={"msg-row " + (isUser ? "user" : "ai")}>
      {!isUser && (
        <div className="msg-avatar ai" aria-hidden>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round">
            <path d="m12 3 4 5-4 13-4-13 4-5Z" fill="rgba(255,255,255,.18)"/>
          </svg>
        </div>
      )}
      <div className="msg-col">
        <div className={"bubble " + (isUser ? "user" : "ai")}>
          {msg.text && renderBody(msg.text)}
          {msg.code && <pre><code>{highlightCode(msg.code)}</code></pre>}
          {streaming && <span className="caret"/>}
          {msg.actions && msg.actions.map((a, ai) => (
            <ActionCard
              key={ai}
              action={a}
              onAccept={() => onActionAccept && onActionAccept(msgIdx, ai)}
              onReject={() => onActionReject && onActionReject(msgIdx, ai)}
            />
          ))}
        </div>
        {!isUser && !streaming && (
          <div className="msg-meta">
            <button className="meta-btn" title="Copy"><I.Copy/></button>
            <button className="meta-btn" title="Regenerate"><I.Refresh/></button>
            <button className="meta-btn" title="Good response"><I.Thumb/></button>
            <button className="meta-btn" title="Bad response"><I.Thumb style={{ transform: "rotate(180deg)" }}/></button>
          </div>
        )}
      </div>
      {isUser && <div className="msg-avatar user">KH</div>}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="msg-row ai">
      <div className="msg-avatar ai" aria-hidden>
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round">
          <path d="m12 3 4 5-4 13-4-13 4-5Z" fill="rgba(255,255,255,.18)"/>
        </svg>
      </div>
      <div className="bubble ai typing">
        <span className="dot"/><span className="dot"/><span className="dot"/>
      </div>
    </div>
  );
}

export function Thread({ messages, isTyping, onActionAccept, onActionReject }) {
  const ref = useRef(null);
  useLayoutEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [messages, isTyping]);

  return (
    <div className="thread" ref={ref}>
      <div className="thread-inner">
        {messages.map((m, i) => (
          <Message
            key={i}
            msg={m}
            msgIdx={i}
            streaming={m.streaming}
            onActionAccept={onActionAccept}
            onActionReject={onActionReject}
          />
        ))}
        {isTyping && <TypingIndicator/>}
      </div>
    </div>
  );
}
