-- Book filter: numbering, cross-references, callouts, sidenotes.
-- Runs twice per chapter. Pass 1 (BOOK_COLLECT set) records every label.
-- Pass 2 (BOOK_LABELS set) resolves references against all chapters.

local chapter = os.getenv("BOOK_CHAPTER") or "0"
local this_file = os.getenv("BOOK_FILE") or ""
local collect_path = os.getenv("BOOK_COLLECT")
local labels_path = os.getenv("BOOK_LABELS")
local single = os.getenv("BOOK_SINGLE") == "1"

-- kind -> {display name, counter group, box class}
local ENVS = {
  definition  = {"Definition", "thm", "thm"},
  theorem     = {"Theorem", "thm", "thm"},
  proposition = {"Proposition", "thm", "thm"},
  lemma       = {"Lemma", "thm", "thm"},
  corollary   = {"Corollary", "thm", "thm"},
  example     = {"Example", "example", "ex"},
  exercise    = {"Exercise", "exercise", "ex"},
  thought     = {"Thought experiment", "thought", "thought"},
  algorithm   = {"Algorithm", "algorithm", "code"},
  remark      = {"Remark", nil, "remark"},
  warning     = {"Pitfall", nil, "remark"},
  proof       = {"Proof", nil, nil},
}

local counters, collected, sections, errors = {}, {}, {}, {}
local known = {}

if labels_path then
  local f = assert(io.open(labels_path))
  known = pandoc.json.decode(f:read("a"), false)
  f:close()
end

local function nextnum(group)
  counters[group] = (counters[group] or 0) + 1
  return chapter .. "." .. counters[group]
end

local function register(id, text)
  if id == nil or id == "" then return end
  if collected[id] then table.insert(errors, "duplicate label: " .. id) end
  collected[id] = {text = text, file = this_file}
end

local function runin(blocks, inlines)
  -- Put a run-in header at the start of the first paragraph of a block list.
  local first = blocks[1]
  if first and (first.t == "Para" or first.t == "Plain") then
    for i = #inlines, 1, -1 do table.insert(first.content, 1, inlines[i]) end
  else
    table.insert(blocks, 1, pandoc.Para(inlines))
  end
end

local sec_counter = {0, 0}

local function handle_header(h)
  if h.level == 1 then
    table.insert(errors, "use front matter `title:` instead of a level-1 heading")
    return h
  end
  if h.level > 3 then return h end
  local title = pandoc.utils.stringify(h.content)
  if h.classes:includes("unnumbered") then
    if not h.identifier:match("^sec") then
      h.identifier = "ch" .. chapter .. "-" .. h.identifier
    end
    if h.level == 2 then
      table.insert(sections, {id = h.identifier, num = "", title = title})
    end
    return h
  end
  local num
  if h.level == 2 then
    sec_counter[1] = sec_counter[1] + 1
    sec_counter[2] = 0
    num = chapter .. "." .. sec_counter[1]
  else
    sec_counter[2] = sec_counter[2] + 1
    num = chapter .. "." .. sec_counter[1] .. "." .. sec_counter[2]
  end
  if h.identifier:match("^sec") then
    register(h.identifier, "Section\u{00a0}" .. num)
  else
    h.identifier = "ch" .. chapter .. "-" .. h.identifier
  end
  if h.level == 2 then
    table.insert(sections, {id = h.identifier, num = num, title = title})
  end
  table.insert(h.content, 1, pandoc.Space())
  table.insert(h.content, 1, pandoc.Span({pandoc.Str(num)}, {class = "secnum"}))
  return h
end

local function handle_div(d)
  if d.classes:includes("table") then
    local num = nextnum("table")
    register(d.identifier, "Table\u{00a0}" .. num)
    for _, b in ipairs(d.content) do
      if b.t == "Table" then
        local head = {pandoc.Strong({pandoc.Str("Table\u{00a0}" .. num .. ".")}), pandoc.Space()}
        if #b.caption.long == 0 then
          b.caption.long = pandoc.Blocks({pandoc.Plain(head)})
        else
          runin(b.caption.long, head)
        end
      end
    end
    return d
  end
  for kind, spec in pairs(ENVS) do
    if d.classes:includes(kind) then
      local name, group, box = spec[1], spec[2], spec[3]
      local label = name
      if group then
        label = name .. "\u{00a0}" .. nextnum(group)
        register(d.identifier, label)
      elseif kind ~= "proof" then
        register(d.identifier, "the " .. name:lower())
      end
      local head
      if kind == "proof" then
        head = {pandoc.Emph({pandoc.Str("Proof.")}), pandoc.Space()}
        local last = d.content[#d.content]
        local qed = pandoc.RawInline("html", '<span class="qed">\u{25a1}</span>')
        if last and (last.t == "Para" or last.t == "Plain") then
          table.insert(last.content, qed)
        else
          table.insert(d.content, pandoc.Plain({qed}))
        end
      else
        head = {pandoc.Span({pandoc.Str(label)}, {class = "env-label"})}
        local title = d.attributes["name"]
        if title then
          local parsed = pandoc.read(title, "markdown").blocks
          local inl = pandoc.utils.blocks_to_inlines(parsed)
          table.insert(inl, 1, pandoc.Str("("))
          table.insert(inl, pandoc.Str(")"))
          table.insert(head, pandoc.Space())
          table.insert(head, pandoc.Span(inl, {class = "env-name"}))
        end
        table.insert(head, pandoc.Span({pandoc.Str(".")}, {class = "env-dot"}))
        table.insert(head, pandoc.Space())
        d.attributes["name"] = nil
      end
      runin(d.content, head)
      d.classes = pandoc.List({"env", kind})
      if box then d.classes:insert("box-" .. box) end
      return d
    end
  end
  return d
end

local function animate_figure(f)
  -- A figure whose image carries anim="file.gif" shows the animation on screen
  -- and the still image in print and for readers who prefer reduced motion.
  return f:walk({
    Image = function(img)
      local anim = img.attributes["anim"]
      if not anim then return nil end
      local alt = pandoc.utils.stringify(img.caption):gsub('"', "&quot;")
      return pandoc.RawInline("html",
        '<img src="' .. anim .. '" class="anim" alt="' .. alt .. '" loading="lazy" />' ..
        '<img src="' .. img.src .. '" class="still" alt="' .. alt .. '" />')
    end,
  })
end

local function handle_figure(f)
  f = animate_figure(f)
  local num = nextnum("figure")
  register(f.identifier, "Figure\u{00a0}" .. num)
  local head = {pandoc.Strong({pandoc.Str("Figure\u{00a0}" .. num .. ".")}), pandoc.Space()}
  if #f.caption.long == 0 then
    f.caption.long = pandoc.Blocks({pandoc.Plain(head)})
  else
    runin(f.caption.long, head)
  end
  return f
end

local function handle_block(b)
  if b.t == "Header" then return handle_header(b) end
  if b.t == "Div" then return handle_div(b) end
  if b.t == "Figure" then return handle_figure(b) end
  return nil
end

local note_counter = 0

local function handle_inline(el)
  if el.t == "Math" then
    local id = el.text:match("\\label%{([^}]+)%}")
    if id then
      if el.mathtype ~= "DisplayMath" then
        table.insert(errors, "\\label in inline math: " .. id)
        return el
      end
      local num = nextnum("equation")
      register(id, "(" .. num .. ")")
      el.text = el.text:gsub("\\label%{[^}]+%}", function() return "\\tag{" .. num .. "}" end)
      return pandoc.Span({el}, {id = id, class = "eqn"}), false
    end
    return nil
  end
  if el.t == "Link" and el.target:sub(1, 1) == "#" then
    local id = el.target:sub(2)
    local hit = known[id]
    if hit and hit.planned then
      -- A chapter that is listed but not written yet: name it, do not link it.
      if #el.content == 0 then return pandoc.Str(hit.text) end
      return pandoc.Span(el.content)
    end
    if hit then
      if #el.content == 0 then el.content = {pandoc.Str(hit.text)} end
      if hit.file ~= this_file and not single then el.target = hit.file .. "#" .. id end
      el.classes:insert("xref")
    elseif labels_path then
      if os.getenv("BOOK_LENIENT") == "1" then
        io.stderr:write("warning " .. this_file .. ": unresolved reference #" .. id .. "\n")
        if #el.content == 0 then el.content = {pandoc.Str("[" .. id .. "]")} end
      else
        table.insert(errors, "unresolved reference: #" .. id)
      end
    end
    return el
  end
  if el.t == "Note" then
    note_counter = note_counter + 1
    local n = tostring(note_counter)
    local body = pandoc.utils.blocks_to_inlines(el.content)
    table.insert(body, 1, pandoc.RawInline("html", '<sup class="sn-num">' .. n .. "</sup> "))
    return {
      pandoc.RawInline("html", '<sup class="sn-ref">' .. n .. "</sup>"),
      pandoc.Span(body, {class = "sidenote"}),
    }
  end
  return nil
end

function Pandoc(doc)
  doc = doc:walk({traverse = "topdown", Block = handle_block})
  doc = doc:walk({traverse = "topdown", Inline = handle_inline})
  if collect_path then
    local f = assert(io.open(collect_path, "w"))
    f:write(pandoc.json.encode({labels = collected, sections = sections}))
    f:close()
  end
  for _, e in ipairs(errors) do io.stderr:write("BOOKERR " .. this_file .. ": " .. e .. "\n") end
  return doc
end
