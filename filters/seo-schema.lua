-- SEO metadata and structured data (JSON-LD) for Open EP Mapping Lab.
--
-- Adds:
--   1. <meta name="robots" content="max-image-preview:large"> on every rendered page.
--   2. LearningResource + BreadcrumbList JSON-LD on every module page (modules/mNN-*.qmd).
--   3. DefinedTermSet JSON-LD on the glossary page (glossary/index.qmd).

local SITE_URL = "https://openepengineering.org/"
local COURSE_NAME = "Open EP Mapping Lab"
local LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"

local function json_escape(s)
  s = tostring(s or "")
  s = s:gsub("\\", "\\\\")
  s = s:gsub('"', '\\"')
  s = s:gsub("\n", "\\n")
  s = s:gsub("\r", "\\r")
  s = s:gsub("\t", "\\t")
  return s
end

local function add_header_html(meta, snippet)
  if quarto and quarto.doc and quarto.doc.include_text then
    quarto.doc.include_text("in-header", snippet)
    return meta
  end
  local block = pandoc.RawBlock("html", snippet)
  local hi = meta["header-includes"]
  if hi == nil then
    meta["header-includes"] = pandoc.MetaList({ pandoc.MetaBlocks({ block }) })
  elseif pandoc.utils.type(hi) == "List" then
    hi:insert(pandoc.MetaBlocks({ block }))
  else
    meta["header-includes"] = pandoc.MetaList({ hi, pandoc.MetaBlocks({ block }) })
  end
  return meta
end

local function input_relpath()
  local f = nil
  if quarto and quarto.doc and quarto.doc.input_file then
    f = quarto.doc.input_file
  elseif PANDOC_STATE and PANDOC_STATE.input_files and #PANDOC_STATE.input_files > 0 then
    f = PANDOC_STATE.input_files[1]
  end
  if not f then
    return ""
  end
  return tostring(f):gsub("\\", "/")
end

function Meta(meta)
  local parts = {
    '<meta name="robots" content="max-image-preview:large">'
  }

  local rel = input_relpath()
  local module_id = meta["module-id"] and pandoc.utils.stringify(meta["module-id"]) or nil
  local title = meta["title"] and pandoc.utils.stringify(meta["title"]) or ""
  local description = meta["description"] and pandoc.utils.stringify(meta["description"]) or ""

  if module_id and module_id ~= "" then
    local stem = rel:match("modules/([^/]+)%.qmd$")
    local page_url = stem and (SITE_URL .. "modules/" .. stem .. ".html") or SITE_URL
    local part_name = meta["part"] and pandoc.utils.stringify(meta["part"]) or ""
    local json = string.format([[<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "LearningResource",
      "name": "%s",
      "description": "%s",
      "url": "%s",
      "inLanguage": "en",
      "isAccessibleForFree": true,
      "license": "%s",
      "learningResourceType": "Course module",
      "educationalLevel": "Graduate / Professional Engineering",
      "isPartOf": {
        "@type": "Course",
        "name": "%s",
        "url": "%s"
      },
      "provider": {
        "@type": "Organization",
        "name": "%s",
        "url": "%s"
      }
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "%s",
          "item": "%s"
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "%s",
          "item": "%scourse-map.html"
        },
        {
          "@type": "ListItem",
          "position": 3,
          "name": "%s",
          "item": "%s"
        }
      ]
    }
  ]
}
</script>]],
      json_escape(title),
      json_escape(description),
      json_escape(page_url),
      LICENSE_URL,
      COURSE_NAME,
      SITE_URL,
      COURSE_NAME,
      SITE_URL,
      COURSE_NAME,
      SITE_URL,
      json_escape(part_name ~= "" and part_name or "Course map"),
      SITE_URL,
      json_escape(title),
      json_escape(page_url)
    )
    table.insert(parts, json)
  elseif rel:match("glossary/index%.qmd$") then
    local page_url = SITE_URL .. "glossary/"
    local json = string.format([[<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "DefinedTermSet",
  "name": "Open EP Mapping Lab Glossary",
  "description": "%s",
  "url": "%s",
  "inLanguage": "en",
  "license": "%s",
  "isPartOf": {
    "@type": "Course",
    "name": "%s",
    "url": "%s"
  }
}
</script>]],
      json_escape(description),
      page_url,
      LICENSE_URL,
      COURSE_NAME,
      SITE_URL
    )
    table.insert(parts, json)
  end

  return add_header_html(meta, table.concat(parts, "\n"))
end
