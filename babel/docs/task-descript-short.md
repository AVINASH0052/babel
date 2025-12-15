# BabelExtreme: Task Description for Apprentice

## What We're Building

We are building a tool that translates scanned books from one language to another. Imagine you have a Japanese engineering textbook that was printed on paper and then scanned into a PDF. There's no way to copy and paste the text because it's just a picture of each page. Our tool will read those pictures, understand what's text and what's a diagram, translate all the text into English, and create a brand new PDF that looks exactly like the original—just in a different language.

## Why This Is Hard

Normal translation tools can't handle scanned documents. If you try to copy text from a scanned PDF, nothing happens because there is no text—only images. Standard tools either fail completely or produce messy results where tables break, diagrams disappear, and mathematical formulas become unreadable. Engineering books are especially difficult because they contain complex layouts with pictures, tables, equations, and technical drawings all mixed together on the same page.

## The Core Idea

Our approach is simple in concept: treat the scanned PDF as a collection of pictures, figure out what each part of the picture represents (is it regular text? a table? a formula? a photo?), extract and translate only the text parts, and then put everything back together in the same positions. The key principle is that we never touch the images, diagrams, or table borders—we only translate the actual words while keeping everything else exactly as it was.

## How It Works (Four Steps)

The system works like an assembly line with four stations. First, we take the PDF apart into individual page images and clean them up if they're crooked or blurry. Second, we use AI to look at each page and identify where the text, tables, formulas, and pictures are located. Third, we send the text to a translation AI and get back the translated version. Fourth, we put everything back together by placing the translated text in the exact same spots where the original text was, creating a new PDF that mirrors the original layout.

## What Makes This Special

Unlike other tools that try to recreate the entire document from scratch (which often fails), we use the original page as our foundation. Think of it like placing new stickers over the old text labels—the underlying picture never changes. This means photos stay sharp, diagram lines stay crisp, and tables keep their structure. We only replace the words, nothing else.

## What You Need to Know

The heavy lifting is done by three main AI tools that already exist and are freely available. MinerU is the "reader" that looks at page images and figures out what each section is. Qwen2.5-VL is the "diagram expert" that can read text labels inside technical drawings. The translation itself uses powerful language models like DeepSeek or Llama. Your job is to wire these tools together into a smooth pipeline and make sure the output PDF looks professional.

## What Success Looks Like

When you're done, someone should be able to upload a 200-page scanned Japanese engineering textbook and receive back a fully translated English version. Every photograph should be identical to the original. Every table should have the same number of rows and columns with only the text translated. Every diagram should show English labels in the same positions where Japanese labels used to be. The translated PDF should also have selectable text, meaning someone can search for words or copy and paste from it.

## Getting Started

Begin by testing MinerU on a single page from a real scanned document. If MinerU can correctly identify where the text, tables, and images are, then the hardest part is already solved. From there, you'll add the translation step and the reconstruction step one at a time. Don't try to build everything at once—get each piece working before connecting them together.
