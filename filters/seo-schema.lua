-- SEO metadata and structured data (JSON-LD) for Open EP Mapping Lab.
--
-- Adds:
--   1. <meta name="robots" content="index, follow, max-image-preview:large"> on every rendered page.
--   2. <meta property="og:url"> and <meta property="og:type"> on every rendered page (Quarto omits both).
--   3. LearningResource + BreadcrumbList JSON-LD on every module page (modules/mNN-*.qmd).
--   4. DefinedTermSet + BreadcrumbList JSON-LD on the glossary page (glossary/index.qmd).
--   5. Page-level schema.org + BreadcrumbList JSON-LD on key top-level pages (about, course-map,
--      formula-sheet, ai-competencies, useful-links).

local SITE_URL = "https://openepengineering.org/"
local REPO_URL = "https://github.com/raghavendrasri/open-ep-mapping-lab"
local COURSE_NAME = "Open EP Mapping Lab"
local ALT_NAME = "Open EP Engineering"
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

local function html_escape(s)
  s = tostring(s or "")
  s = s:gsub("&", "&amp;")
  s = s:gsub('"', "&quot;")
  s = s:gsub("<", "&lt;")
  s = s:gsub(">", "&gt;")
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

local function canonical_url_for(rel)
  local mod_stem = rel:match("modules/([^/]+)%.qmd$")
  if mod_stem then
    return SITE_URL .. "modules/" .. mod_stem .. ".html", "module"
  end
  if rel:match("glossary/index%.qmd$") then
    return SITE_URL .. "glossary/", "glossary"
  end
  if rel:match("formula%-sheet/index%.qmd$") then
    return SITE_URL .. "formula-sheet/", "formula-sheet"
  end
  local top = rel:match("([^/]+)%.qmd$")
  if top == "index" then
    return SITE_URL, "home"
  elseif top then
    return SITE_URL .. top .. ".html", top
  end
  return SITE_URL, "other"
end

local function top_level_jsonld(schema_type, name, description, page_url, crumb_name)
  return string.format([[<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "%s",
      "name": "%s",
      "description": "%s",
      "url": "%s",
      "inLanguage": "en",
      "license": "%s",
      "isPartOf": {
        "@type": "WebSite",
        "@id": "%s#website",
        "name": "%s",
        "alternateName": "%s",
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
          "item": "%s"
        }
      ]
    }
  ]
}
</script>]],
    schema_type,
    json_escape(name),
    json_escape(description),
    json_escape(page_url),
    LICENSE_URL,
    SITE_URL,
    COURSE_NAME,
    ALT_NAME,
    SITE_URL,
    COURSE_NAME,
    SITE_URL,
    json_escape(crumb_name),
    json_escape(page_url)
  )
end

function Meta(meta)
  local rel = input_relpath()
  local page_url, kind = canonical_url_for(rel)
  local og_type = (kind == "module") and "article" or "website"

  local parts = {
    '<meta name="robots" content="index, follow, max-image-preview:large">',
    string.format('<meta property="og:url" content="%s">', html_escape(page_url)),
    string.format('<meta property="og:type" content="%s">', og_type),
  }

  local module_id = meta["module-id"] and pandoc.utils.stringify(meta["module-id"]) or nil
  local title = meta["title"] and pandoc.utils.stringify(meta["title"]) or ""
  local description = meta["description"] and pandoc.utils.stringify(meta["description"]) or ""

  if module_id and module_id ~= "" then
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
        "@id": "%s#course",
        "name": "%s",
        "url": "%s"
      },
      "provider": {
        "@type": "Organization",
        "@id": "%s#organization",
        "name": "%s",
        "alternateName": "%s",
        "url": "%s",
        "sameAs": ["%s"]
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
      SITE_URL,
      COURSE_NAME,
      SITE_URL,
      SITE_URL,
      COURSE_NAME,
      ALT_NAME,
      SITE_URL,
      REPO_URL,
      COURSE_NAME,
      SITE_URL,
      json_escape(part_name ~= "" and part_name or "Course map"),
      SITE_URL,
      json_escape(title),
      json_escape(page_url)
    )
    table.insert(parts, json)
  elseif kind == "glossary" then
    table.insert(parts, top_level_jsonld("DefinedTermSet", "Open EP Mapping Lab Glossary", description, page_url, "Glossary"))
  elseif kind == "formula-sheet" then
    table.insert(parts, top_level_jsonld("LearningResource", "Open EP Mapping Lab Formula Sheet", description, page_url, "Formula sheet"))
  elseif kind == "about" then
    table.insert(parts, top_level_jsonld("AboutPage", "About Open EP Mapping Lab", description, page_url, "About"))
  elseif kind == "course-map" then
    table.insert(parts, top_level_jsonld("CollectionPage", "Course Map — Open EP Mapping Lab", description, page_url, "Course map"))
  elseif kind == "useful-links" then
    table.insert(parts, top_level_jsonld("CollectionPage", "Useful Links — Open EP Mapping Lab", description, page_url, "Useful links"))
  elseif kind == "ai-competencies" then
    table.insert(parts, top_level_jsonld("LearningResource", "AI Competencies — Open EP Mapping Lab", description, page_url, "AI competencies"))
  end

  return add_header_html(meta, table.concat(parts, "\n"))
end
