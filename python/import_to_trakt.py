import csv

reader = csv.DictReader('shows.csv', delimiter=',')
read_ids = list(reader)

for myid in read_ids:
    # If id (row) exists and is not blank (has a format)
    if myid and not options.format in myid:
        print(
            "Invalid file format, id (row) must exists and is not blank (has a format).")
        sys.exit(1)
    if myid and myid[options.format]:
        # pp.pprint(myid)
        # If format is not "imdb" it must be cast to an integer
        if not options.format == "imdb" and not myid[options.format].startswith('tt'):
            myid[options.format] = int(myid[options.format])
        if (options.type == "movies" or options.type == "shows") and options.seen:
            data.append(
                {'ids': {options.format: myid[options.format]}, "watched_at": options.seen})
        elif (options.type == "movies" or options.type == "shows") and options.watched_at:
            data.append(
                {'ids': {options.format: myid[options.format]}, "watched_at": myid["watched_at"]})
        elif options.type == "episodes" and options.seen:
            data.append(
                {'ids': {options.format: myid[options.format]}, "watched_at": options.seen})
        elif options.type == "episodes" and options.watched_at:
            data.append(
                {'ids': {options.format: myid[options.format]}, "watched_at": myid["watched_at"]})
        elif (options.type == "movies" or options.type == "shows") and options.list == 'ratings' and options.rated_at:
            data.append({'ids': {
                        options.format: myid[options.format]}, "rated_at": myid["rated_at"], "rating": myid["rating"]})
        else:
            data.append(
                {'ids': {options.format: myid[options.format]}})
        # Import batch of 10 IDs
        if len(data) >= 10:
            # pp.pprint(json.dumps(data))
            results['sentids'] += len(data)
            result = api_add_to_list(options, data)
            if result:
                print("Result: {0}".format(result))
                if 'added' in result and result['added']:
                    results['added'] += result['added'][options.type]
                if 'existing' in result and result['existing']:
                    results['existing'] += result['existing'][options.type]
                if 'not_found' in result and result['not_found']:
                    results['not_found'] += len(
                        result['not_found'][options.type])
            data = []
# Import the rest
if len(data) > 0:
    # pp.pprint(data)
    results['sentids'] += len(data)
    result = api_add_to_list(options, data)
    if result:
        print("Result: {0}".format(result))
        if 'added' in result and result['added']:
            results['added'] += result['added'][options.type]
        if 'existing' in result and result['existing']:
            results['existing'] += result['existing'][options.type]
        if 'not_found' in result and result['not_found']:
            results['not_found'] += len(result['not_found']
                                        [options.type])