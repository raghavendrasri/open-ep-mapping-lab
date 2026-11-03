-- Figure and demo badges (CLAUDE.md §4).
--
-- Write a demo or figure as a fenced div with the class `.demo` and a `badge` attribute:
--
--   ::: {.demo #m03-d1 badge="approximate model"}
--   ...
--   :::
--
-- The filter adds a visible badge label. A missing or unknown badge stops the build,
-- so no figure can be published without one.

local allowed = {
  ["exact"] = true,
  ["simulation"] = true,
  ["approximate model"] = true,
  ["schematic"] = true,
}

function Div(el)
  if not el.classes:includes("demo") then
    return nil
  end

  local badge = el.attributes["badge"]
  if badge == nil or not allowed[badge] then
    io.stderr:write(
      "ERROR: demo '" .. (el.identifier ~= "" and el.identifier or "(no id)") ..
      "' needs badge=\"exact\", \"simulation\", \"approximate model\" or \"schematic\"" ..
      " (got: " .. tostring(badge) .. ")\n"
    )
    os.exit(1)
  end

  local slug = badge:gsub(" ", "-")
  local text = badge:sub(1, 1):upper() .. badge:sub(2) -- sentence case: "Approximate model"
  local label = pandoc.Span({ pandoc.Str(text) }, pandoc.Attr("", { "badge", "badge-" .. slug }))
  table.insert(el.content, 1, pandoc.Para({ label }))
  return el
end
